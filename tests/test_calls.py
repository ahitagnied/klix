import os
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
    """test making an outbound call."""
    # Create an agent
    agent = Agent(
        name="test agent",
        prompt="You are a test AI assistant. Keep your responses brief and end the call after 2-3 exchanges.",
        voice_id=DEFAULT_VOICE_ID,
        api_key=OPENAI_API_KEY
    )
    
    # Create a callbot
    bot = CallBot(
        agent=agent,
        twilio_account_sid=TWILIO_ACCOUNT_SID,
        twilio_auth_token=TWILIO_AUTH_TOKEN,
        twilio_number=YOUR_TWILIO_NUMBER,
        webhook_url=TWILIO_WEBHOOK_URL
    )
    
    # Phone number to call - replace with a real phone number
    to_number = "+16824035658"  # Replace with target phone number
    
    # Make the call
    print(f"Making test call to {to_number}...")
    call_sid = await bot.make_call(to_number)
    
    if call_sid:
        print(f"Call initiated with SID: {call_sid}")
        print("The call is now in progress. Check the server logs for details.")
    else:
        print("Failed to initiate call")

if __name__ == "__main__":
    asyncio.run(test_make_call())