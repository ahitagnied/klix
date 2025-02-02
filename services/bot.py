from twilio.rest import Client
from openai import OpenAI
from ..config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, OPENAI_API_KEY, YOUR_TWILIO_NUMBER, YOUR_WEBHOOK_URL
from ..models.agent import Agent
from twilio.twiml.voice_response import VoiceResponse, Say, Start, Stream
from ..models.scenario import Scenario

class CallBot:
    def __init__(self, agent: Agent, scenario: Scenario):
        self.agent = agent
        self.scenario = scenario
        self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    def generate_twiml():
        response = VoiceResponse()



    async def make_call():
        pass

    async def handle_websocket(self, websocket):
        # 1. Get audio from call
        # 2. Convert to text
        response = await self.agent.get_response(text)
        # 3. Convert response to audio
        # 4. Send back to call

    