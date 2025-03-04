# tests/test_calls.py
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from models.agent import Agent
from services.bot import CallBot
from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, OPENAI_API_KEY,
    YOUR_TWILIO_NUMBER, TWILIO_WEBHOOK_URL, DEFAULT_VOICE_ID
)

async def test_make_call():
    """Test making an outbound call."""
    agent = Agent(
        name="Test Agent",
        prompt="You are a test AI assistant. Keep responses brief and end the call after a few exchanges.",
        voice_id=DEFAULT_VOICE_ID,
        api_key=OPENAI_API_KEY
    )
    
    bot = CallBot(
        agent=agent,
        twilio_account_sid=TWILIO_ACCOUNT_SID,
        twilio_auth_token=TWILIO_AUTH_TOKEN,
        twilio_number=YOUR_TWILIO_NUMBER,
        webhook_url=TWILIO_WEBHOOK_URL
    )
    
    # Replace with a real phone number for testing.
    to_number = "+16824035658"
    print(f"Making test call to {to_number}...")
    call_sid = await bot.make_call(to_number)
    
    if call_sid:
        print(f"Call initiated with SID: {call_sid}")
        print("The call is now in progress. Check the server logs for conversation details.")
    else:
        print("Failed to initiate call")

if __name__ == "__main__":
    asyncio.run(test_make_call())