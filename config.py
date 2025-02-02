import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys (loaded from environment)
OPENAI_API_KEY = os.getenv("k-proj-SnkLDa7EVsxQZrtU3qFN23_fhsBV_mgSWLw---I1YILy1zlgBQ1daPPwaS2svokAb5K48IqkgHT3BlbkFJrWLGElAFRzF-QAhyVJoxUR_wAnSKND7SSSYCpoNb0e_AnxzYlIHHKM0ADUsbUuW5s74Cd2_QAA")
TWILIO_ACCOUNT_SID = os.getenv("AC67373569963fbb25b6edbf04619be170")
TWILIO_AUTH_TOKEN = os.getenv("688ceabc3bf25ecfdcbbbcb02e20ba90")

# Application settings (hardcoded defaults)
DEFAULT_VOICE_ID = "default-voice-id"
SERVER_PORT = 8765
MAX_RETRIES = 3
AUDIO_CHUNK_SIZE = 1024
SAMPLE_RATE = 16000

# API endpoints
TWILIO_WEBHOOK_URL = "https://your-webhook-url.com"