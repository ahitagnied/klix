from twilio.rest import Client
from openai import OpenAI
from twilio.twiml.voice_response import VoiceResponse, Say, Start, Stream
from dataclasses import dataclass
import sys
from pathlib import Path
import asyncio
import json
from typing import Optional

# add the project root to the Python path
root_dir = Path(__file__).parent.parent  # go up one level from current file
sys.path.append(str(root_dir))

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, OPENAI_API_KEY, YOUR_TWILIO_NUMBER, YOUR_WEBHOOK_URL
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
        stream = Stream(name='audio_stream', url=f'{self.webhook_url}/stream')
        
        # set stream parameters
        stream.parameter(name='direction', value='duplex')
        stream.parameter(name='mediaFormat', value='audio/webm')
        
        start.append(stream)
        response.append(start)
        
        return response

    async def handle_websocket(self, websocket, path):
        """
        handle websocket connection for real-time audio streaming.
        
        args:
            websocket: websocket connection object
            path: websocket path
        """
        call_sid = None
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data.get('event') == 'start':
                    call_sid = data.get('call_sid')
                    self.active_calls[call_sid] = {
                        'websocket': websocket,
                        'transcript': ''
                    }
                
                elif data.get('event') == 'media':
                    if not call_sid:
                        continue
                        
                    # convert audio chunk to text using openai whisper
                    audio_data = data.get('media').get('payload')
                    transcript = await self._convert_audio_to_text(audio_data)
                    
                    if transcript:
                        # get response from agent
                        response = await self.agent.get_response(transcript)
                        
                        # convert response to audio using openai tts
                        audio_response = await self._convert_text_to_audio(response)
                        
                        # send audio back through websocket
                        await websocket.send(json.dumps({
                            'event': 'media',
                            'media': {
                                'payload': audio_response
                            }
                        }))
                
                elif data.get('event') == 'stop':
                    if call_sid and call_sid in self.active_calls:
                        del self.active_calls[call_sid]
                    
        except Exception as e:
            print(f"error in websocket handler: {str(e)}")
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
            # create a temporary file with the audio data
            # note: you'll need to handle the audio format conversion if needed
            response = self.agent.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data
            )
            return response.text
        except Exception as e:
            print(f"error converting audio to text: {str(e)}")
            return ""

    async def _convert_text_to_audio(self, text: str) -> bytes:
        """
        convert text to audio using openai tts.
        """
        try:
            response = self.agent.client.audio.speech.create(
                model="tts-1",
                voice=self.agent.voice_id,
                input=text
            )
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