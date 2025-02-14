import asyncio
import sys
from pathlib import Path

# add the project root to the Python path
root_dir = Path(__file__).parent.parent  # go up one level from current file
sys.path.append(str(root_dir))

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, YOUR_TWILIO_NUMBER, OPENAI_API_KEY, DEFAULT_VOICE_ID
from models.agent import Agent
from services.bot import CallBot

# Create an instance of your Agent (customize this as needed)
agent = Agent(name='test', prompt='you are a helpful agent, engage in a conversation', api_key=OPENAI_API_KEY, voice_id=DEFAULT_VOICE_ID)

# Replace with your actual webhook base URL (e.g., using ngrok for local testing)
webhook_url = "https://your-webhook-url.com"

# Create the CallBot instance
callbot = CallBot(
    agent=agent,
    twilio_account_sid=TWILIO_ACCOUNT_SID,
    twilio_auth_token=TWILIO_AUTH_TOKEN,
    twilio_number=YOUR_TWILIO_NUMBER,
    webhook_url=webhook_url
)

async def main():
    # Replace '+6824035658' with the outbound number you want to call
    call_sid = await callbot.make_call("+16824035658")
    if call_sid:
        print(f"Call initiated successfully with SID: {call_sid}")
    else:
        print("Failed to initiate call.")

if __name__ == '__main__':
    asyncio.run(main())