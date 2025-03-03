import io
import sys
from pathlib import Path
import asyncio

root_dir = Path(__file__).parent.parent  # go up one level from current file
sys.path.append(str(root_dir))

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, YOUR_TWILIO_NUMBER, OPENAI_API_KEY, DEFAULT_VOICE_ID
from models.agent import Agent
from services.bot import CallBot
from models.agent import Agent

# Create an instance of your Agent (customize this as needed)
agent = Agent(name='test', prompt='you are a helpful agent, engage in a conversation', api_key=OPENAI_API_KEY, voice_id='sage')

# Replace with your actual webhook base URL (e.g., using ngrok for local testing)
webhook_url = "wss://d72d-168-4-86-45.ngrok-free.app"

callbot = CallBot(
    agent=agent,
    twilio_account_sid=TWILIO_ACCOUNT_SID,
    twilio_auth_token=TWILIO_AUTH_TOKEN,
    twilio_number=YOUR_TWILIO_NUMBER,
    webhook_url=webhook_url
)

# async def main():
#     # open mp3 in binary mode
#     with open("stt_test.mp3", "rb") as f:
#         mp3_bytes = f.read()

#     # wrap bytes in BytesIO
#     audio_file = io.BytesIO(mp3_bytes)
#     audio_file.name = "stt_test.mp3"  # let whisper know it's mp3

#     # now await the async method
#     transcript = await callbot._convert_audio_to_text(audio_file)
#     print("transcript:", transcript)

async def main():
    # the text we want to convert to audio
    test_text = "Hello! This is a test of the AI TTS function."

    # call the async tts method
    audio_bytes = await callbot._convert_text_to_audio(test_text)

    # write result to a file so we can listen
    output_file = "tts_test_output.wav"
    with open(output_file, "wb") as f:
        f.write(audio_bytes)

    print(f"TTS audio written to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
