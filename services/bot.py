from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say, Start, Stream
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass
import asyncio
import json
import os
import sys
from pathlib import Path

# add the project root to the python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, OPENAI_API_KEY, YOUR_TWILIO_NUMBER, TWILIO_WEBHOOK_URL, DEEPGRAM_API_KEY, CARTESIA_API_KEY

# import pipecat modules
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, EndTaskFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams, FastAPIWebsocketTransport

from models.agent import Agent

class CallBot:
    def __init__(self, agent: Agent, twilio_account_sid: str, twilio_auth_token: str, 
                 twilio_number: str, webhook_url: str):
        """
        initialize callbot with an agent and twilio credentials.
        """
        self.agent = agent
        self.twilio_number = twilio_number
        self.webhook_url = webhook_url  # base url for your streaming endpoint
        self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
        self.active_calls = {}  # tracking active calls

    def generate_twiml(self) -> str:
        """
        generate twiml for call setup with websocket streaming.
        """
        response = VoiceResponse()
        response.say("hello, i'm connecting you with an ai assistant.")

        start = Start()
        # the streaming url should point to your fastapi websocket endpoint.
        stream = Stream(name="audio_stream", url=f"{self.webhook_url}/ws/stream")
        stream.parameter(name="direction", value="duplex")
        stream.parameter(name="mediaformat", value="audio/webm")
        start.append(stream)
        response.append(start)

        # hold the call open for a while.
        response.pause(length=3600)
        return str(response)

    async def run_pipeline(self, websocket: WebSocket, call_sid: str):
        """
        set up and run the pipecat pipeline using the connected websocket.
        """
        # initialize twilio streaming transport with pipecat.
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
                serializer=TwilioFrameSerializer(call_sid),  # using call_sid as stream identifier
            ),
        )

        # set up the openai llm service.
        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY") or "", model="gpt-4o")
        # register an end_call function so that the llm can trigger call termination.
        llm.register_function("end_call", self.end_call)

        # optionally, define any tools (functions) your llm may call.
        tools = [
            {
                "name": "end_call",
                "description": "ends the call when invoked."
            }
        ]

        # set up stt and tts services.
        stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
        tts = CartesiaTTSService(
            api_key=os.getenv("CARTESIA_API_KEY") or "",
            voice_id=self.agent.voice_id,
        )

        # build the initial conversation context.
        messages = [
            {"role": "system", "content": self.agent.prompt},
            {"role": "system", "content": "you are connected to an ai voice assistant."},
            {"role": "system", "content": "please end the call if the user says goodbye."}
        ]
        context = OpenAILLMContext(messages, tools)
        context_aggregator = llm.create_context_aggregator(context)

        # build the pipeline with the following stages:
        pipeline = Pipeline([
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ])

        # create and run the pipeline task.
        task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)

        # after the pipeline run ends, you can do any cleanup here.
        return messages

    async def end_call(self, function_name, tool_call_id, args, llm, context, result_callback):
        """
        called from the llm to end the call.
        """
        print("ending call per llm request.")
        # update the call with twilio to hang up.
        try:
            self.twilio_client.calls(args.get("call_sid")).update(twiml="<response><hangup/></response>")
        except Exception as e:
            print(f"error ending call: {e}")
        # send an end-task frame upstream.
        await llm.push_frame(EndTaskFrame(), None)

    
    async def handle_websocket(self, websocket: WebSocket):
        """
        handle an incoming websocket connection for a call.
        this method sets up and runs the pipecat pipeline.
        """
        call_sid = None
        try:
            # wait for messages until a "start" event is received.
            while True:
                message = await websocket.receive_text()
                print("debug: message received:", message)
                data = json.loads(message)
                event = data.get("event")
                if event == "connected":
                    print("debug: received connected event, waiting for start event")
                    continue
                elif event == "start":
                    # extract call sid from the nested "start" field.
                    start_data = data.get("start", {})
                    call_sid = start_data.get("callSid") or start_data.get("call_sid")
                    if call_sid is None:
                        print("debug: start event received but no call sid found; keys:", list(data.keys()))
                        return
                    self.active_calls[call_sid] = {"websocket": websocket}
                    print(f"call started with sid: {call_sid}")
                    break
                else:
                    print(f"debug: received unexpected event '{event}', ignoring")
            # run the pipecat pipeline with this websocket and call_sid.
            await self.run_pipeline(websocket, call_sid)
        except WebSocketDisconnect:
            print("websocket disconnected")
        except Exception as e:
            print(f"error in websocket handler: {e}")
        finally:
            if call_sid and call_sid in self.active_calls:
                del self.active_calls[call_sid]

    async def make_call(self, to_number: str) -> str:
        """
        initiate an outbound call using twilio.
        """
        try:
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.twilio_number,
                twiml=self.generate_twiml()
            )
            return call.sid
        except Exception as e:
            print(f"error making call: {e}")
            return None