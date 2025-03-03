from twilio.rest import Client
from openai import OpenAI
from twilio.twiml.voice_response import VoiceResponse, Say, Start, Stream
from dataclasses import dataclass
from fastapi import WebSocket, WebSocketDisconnect
import sys
from pathlib import Path
import asyncio
import json
from typing import Optional
import base64
import io

# add the project root to the Python path
root_dir = Path(__file__).parent.parent  # go up one level from current file
sys.path.append(str(root_dir))

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, OPENAI_API_KEY, YOUR_TWILIO_NUMBER, TWILIO_WEBHOOK_URL
from models.agent import Agent

from dotenv import load_dotenv

load_dotenv()

class CallBot:
    def __init__(self, agent: Agent, twilio_account_sid: str, twilio_auth_token: str, 
                 twilio_number: str, webhook_url: str):
        """
        initialize callbot with an agent and twilio credentials.
        
        args:
            agent: an instance of the agent class
            twilio_account_sid: twilio account sid
            twilio_auth_token: twilio auth token
            twilio_number: your twilio phone number
            webhook_url: webhook url for handling real-time audio
        """
        self.agent = agent
        self.twilio_number = twilio_number
        self.webhook_url = webhook_url
        self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
        self.active_calls = {}  # store active call sessions
        
    def generate_twiml(self) -> VoiceResponse:
        """
        generate twiml for initial call setup with websocket streaming.
        """
        response = VoiceResponse()
        
        # start with a greeting
        response.say("Hello, I'm connecting you with an AI assistant.")
        
        # start streaming
        start = Start()
        stream = Stream(name='audio_stream', url=f"{TWILIO_WEBHOOK_URL}/ws/stream")
        
        # set stream parameters
        stream.parameter(name='direction', value='duplex')
        stream.parameter(name='mediaFormat', value='audio/webm')
        
        start.append(stream)
        response.append(start)

        response.pause(length=3600)
        
        return response
    
    async def handle_websocket(self, websocket: WebSocket, path: str):
        """
        handle websocket connection for real-time audio streaming.
        
        args:
            websocket: the websocket connection object.
            path: the websocket path.
        """
        call_sid = None
        print("websocket connected!")
        try:
            while True:
                # receive a text message (twilio sends json in text frames)
                message_str = await websocket.receive_text()
                data = json.loads(message_str)
                print(data)
                event = data.get('event')
                if event == 'start':
                    call_sid = data.get('call_sid')
                    self.active_calls[call_sid] = {
                        'websocket': websocket,
                        'transcript': ''
                    }

                elif event == 'media':
                    if not call_sid:
                        continue
                    base64_payload = data['media']['payload']
                    raw_audio = base64.b64decode(base64_payload)

                    audio_file = io.BytesIO(raw_audio)
                    audio_file.name = "audio.webm"  # or audio.wav, etc.

                    transcript = await self._convert_audio_to_text(audio_file)
                    if transcript:
                        # get response from agent
                        response_text = await self.agent.get_response(transcript)
                        print(f"user said: {transcript}")
                        print(f"agent replied: {response_text}")

                        # convert response to audio
                        audio_response = await self._convert_text_to_audio(response_text)
                        # send base64-encoded audio back
                        await websocket.send_text(json.dumps({
                            "event": "media",
                            "media": {
                                "payload": base64.b64encode(audio_response).decode("utf-8")
                            }
                        }))

                elif event == 'stop':
                    if call_sid and call_sid in self.active_calls:
                        del self.active_calls[call_sid]
                    break  # end the loop because the call ended

        except WebSocketDisconnect:
            print("websocket disconnected")
            if call_sid and call_sid in self.active_calls:
                del self.active_calls[call_sid]
        except Exception as e:
            print(f"error in websocket handler: {e}")
            if call_sid and call_sid in self.active_calls:
                del self.active_calls[call_sid]

    async def make_call(self, to_number: str) -> Optional[str]:
        """
        initiate a call to the specified number.
        
        args:
            to_number: the phone number to call
            
        returns:
            str: call sid if successful, none otherwise
        """
        try:
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.twilio_number,
                twiml=str(self.generate_twiml())
            )
            return call.sid
        except Exception as e:
            print(f"error making call: {str(e)}")
            return None

    async def _convert_audio_to_text(self, audio_data: bytes) -> str:
        """
        convert audio data to text using openai whisper.
        """
        try:
            audio_len = len(audio_data.getvalue())
            print(f"debug: about to transcribe audio chunk of size {audio_len} bytes")
            # create a temporary file with the audio data
            # note: you'll need to handle the audio format conversion if needed
            response = await self.agent.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data
            )
            print(f"debug: whisper transcription result: {response.text}")
            return response.text
        except Exception as e:
            print(f"error converting audio to text: {str(e)}")
            return ""

    async def _convert_text_to_audio(self, text: str) -> bytes:
        """
        convert text to audio using openai tts.
        """
        try:
            print(f"debug: about to generate audio for text: '{text}'")
            response = await self.agent.client.audio.speech.create(
                model="tts-1",
                voice=self.agent.voice_id,
                input=text
            )
            print("debug: successfully generated tts audio")
            return response.content
        except Exception as e:
            print(f"error converting text to audio: {str(e)}")
            return b""

    async def close(self):
        """
        clean up resources and end all active calls.
        """
        try:
            # end all active calls
            for call_sid in self.active_calls:
                try:
                    self.twilio_client.calls(call_sid).update(status="completed")
                except Exception as e:
                    print(f"error ending call {call_sid}: {str(e)}")
            
            # clear active calls
            self.active_calls.clear()
            
            # close agent
            await self.agent.close()
            
        except Exception as e:
            print(f"error during cleanup: {str(e)}")