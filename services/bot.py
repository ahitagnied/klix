from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say, Start, Stream
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, OPENAI_API_KEY,
    YOUR_TWILIO_NUMBER, TWILIO_WEBHOOK_URL, DEEPGRAM_API_KEY, CARTESIA_API_KEY
)

# Import pipecat modules
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, EndTaskFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams, FastAPIWebsocketTransport

from models.agent import Agent

class DebugUserLogger(FrameProcessor):
    """Logs what the user said if the frame has a 'text' attribute."""
    async def process_frame(self, frame, direction):
        if hasattr(frame, "text"):
            print(f"User said: {frame.text}")
        return [frame]

class DebugAssistantLogger(FrameProcessor):
    """Logs what the assistant replied if the frame has a 'content' attribute."""
    async def process_frame(self, frame, direction):
        if hasattr(frame, "role") and frame.role == "assistant":
            if hasattr(frame, "content"):
                print(f"Assistant replied: {frame.content}")
            else:
                print("Assistant replied: (no 'content' attribute)")
        return [frame]

class GenericDebugLogger(FrameProcessor):
    """Logs every frame type and its attributes for debugging."""
    async def process_frame(self, frame, direction):
        try:
            # Attempt to print the frame's dictionary representation
            attrs = frame.__dict__
        except Exception:
            attrs = str(frame)
        print(f"Frame type: {type(frame)}, Attributes: {attrs}")
        return [frame]

class CallBot:
    def __init__(self, agent: Agent, twilio_account_sid: str, twilio_auth_token: str, 
                 twilio_number: str, webhook_url: str):
        """Initialize CallBot with an agent and Twilio credentials."""
        self.agent = agent
        self.twilio_number = twilio_number
        self.webhook_url = webhook_url  # Base URL for your streaming endpoint
        self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
        self.active_calls = {}  # Tracking active calls

    def generate_twiml(self) -> str:
        """Generate TwiML for call setup with WebSocket streaming."""
        response = VoiceResponse()
        response.say("Hello, I'm connecting you with an AI assistant.")

        start = Start()
        # The streaming URL should point to your FastAPI WebSocket endpoint
        stream = Stream(name="audio_stream", url=f"{self.webhook_url}/ws/stream")
        stream.parameter(name="direction", value="duplex")
        stream.parameter(name="mediaformat", value="audio/webm")
        start.append(stream)
        response.append(start)

        # Hold the call open for a while
        response.pause(length=3600)
        return str(response)

    async def run_pipeline(self, websocket: WebSocket, call_sid: str):
        """Set up and run the pipecat pipeline using the connected websocket."""
        print(f"Starting pipeline for call SID: {call_sid}")
        
        # Initialize Twilio streaming transport with pipecat
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
                serializer=TwilioFrameSerializer(call_sid),  # Using call_sid as stream identifier
            ),
        )

        # Set up the OpenAI LLM service
        llm = OpenAILLMService(api_key=OPENAI_API_KEY, model="gpt-4o")
        # Register an end_call function so that the LLM can trigger call termination
        llm.register_function("end_call", self.end_call)

        # Optionally, define any tools (functions) your LLM may call
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "end_call",
                    "description": "Ends the call when invoked."
                }
            }
        ]

        # Set up STT and TTS services
        stt = DeepgramSTTService(api_key=DEEPGRAM_API_KEY)
        tts = CartesiaTTSService(
            api_key=CARTESIA_API_KEY,
            voice_id=self.agent.voice_id,
        )

        # Build the initial conversation context
        messages = [
            {"role": "system", "content": self.agent.prompt},
            {"role": "system", "content": "You are connected to an AI voice assistant."},
            {"role": "system", "content": "Please end the call if the user says goodbye."}
        ]
        context = OpenAILLMContext(messages, tools)
        context_aggregator = llm.create_context_aggregator(context)

        # Build the pipeline with debug processors inserted
        pipeline = Pipeline([
            transport.input(),             # Receives audio from Twilio
            stt,                           # STT transcribes audio to text
            DebugUserLogger(),             # Logs what the user said
            context_aggregator.user(),     # Packages user messages for the LLM
            llm,                           # LLM processes user messages
            DebugAssistantLogger(),        # Logs what the assistant replied
            tts,                           # TTS converts the LLM response to audio
            transport.output(),            # Sends audio back to Twilio
            context_aggregator.assistant(),# Updates conversation context with the assistant message
        ])

        # Create and run the pipeline task
        task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
        runner = PipelineRunner(handle_sigint=False)
        
        # Add event handlers for client connections
        async def on_client_connected(transport, client):
            print(f"Client connected for call {call_sid}")
            # You can optionally send an initial greeting here
        
        async def on_client_disconnected(transport, client):
            print(f"Client disconnected for call {call_sid}")
            await task.queue_frames([EndFrame()])
        
        transport.event_handler("on_client_connected")(on_client_connected)
        transport.event_handler("on_client_disconnected")(on_client_disconnected)
        
        await runner.run(task)

        # After the pipeline run ends, return the conversation messages
        return messages

    async def end_call(self, function_name, tool_call_id, args, llm, context, result_callback):
        """Called from the LLM to end the call."""
        print("Ending call per LLM request.")
        try:
            self.twilio_client.calls(args.get("call_sid")).update(
                twiml="<Response><Hangup/></Response>"
            )
        except Exception as e:
            print(f"Error ending call: {e}")
        await llm.push_frame(EndTaskFrame(), FrameDirection.UPSTREAM)

    async def handle_websocket(self, websocket: WebSocket):
        """
        Handle an incoming WebSocket connection for a call.
        This method sets up and runs the pipecat pipeline.
        """
        call_sid = None
        try:
            # Wait for messages until a "start" event is received
            while True:
                message = await websocket.receive_text()
                print(f"WebSocket message received: {message}")
                data = json.loads(message)
                event = data.get("event")
                
                if event == "connected":
                    print("Received connected event, waiting for start event")
                    continue
                elif event == "start":
                    # Extract call sid from the nested "start" field
                    start_data = data.get("start", {})
                    call_sid = start_data.get("callSid") or start_data.get("call_sid")
                    stream_sid = start_data.get("streamSid") or start_data.get("stream_sid")
                    
                    if call_sid is None:
                        print(f"Start event received but no call SID found; keys: {list(data.keys())}")
                        if start_data:
                            print(f"Start data keys: {list(start_data.keys())}")
                        return
                        
                    print(f"Call started with SID: {call_sid}, Stream SID: {stream_sid}")
                    self.active_calls[call_sid] = {
                        "websocket": websocket,
                        "stream_sid": stream_sid
                    }
                    break
                else:
                    print(f"Received unexpected event '{event}', ignoring")
            
            # Run the pipecat pipeline with this websocket and call_sid
            await self.run_pipeline(websocket, call_sid or stream_sid)
            
        except WebSocketDisconnect:
            print("WebSocket disconnected")
        except Exception as e:
            print(f"Error in websocket handler: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if call_sid and call_sid in self.active_calls:
                del self.active_calls[call_sid]

    async def make_call(self, to_number: str) -> str:
        """Initiate an outbound call using Twilio."""
        try:
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.twilio_number,
                twiml=self.generate_twiml()
            )
            print(f"Call initiated to {to_number} with SID: {call.sid}")
            return call.sid
        except Exception as e:
            print(f"Error making call: {e}")
            import traceback
            traceback.print_exc()
            return None