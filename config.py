import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys (loaded from environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Application settings (hardcoded defaults)
DEFAULT_VOICE_ID = 'sage'
CARTESIA_API_KEY='sk_car_fY2tTPfEj58hXUSlQIDCD'
YOUR_TWILIO_NUMBER=os.getenv("YOUR_TWILIO_NUMBER")
SERVER_PORT = 8765
MAX_RETRIES = 3
AUDIO_CHUNK_SIZE = 1024
SAMPLE_RATE = 16000
DEEPGRAM_API_KEY='4590a5f4-531a-4f68-8943-a8ad74d91580'

# API endpoints
TWILIO_WEBHOOK_URL = os.getenv("TWILIO_WEBHOOK_URL")