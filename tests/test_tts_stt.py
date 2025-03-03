import os
import io
import sys
import json
import base64
import asyncio
from pathlib import Path

# add the project root to the python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from config import DEEPGRAM_API_KEY, CARTESIA_API_KEY, OPENAI_API_KEY, DEFAULT_VOICE_ID, TWILIO_WEBHOOK_URL
from models.agent import Agent
from services.bot import CallBot

class DummyWebsocket:
    """
    a dummy websocket to simulate twilio media stream messages.
    """
    def __init__(self, messages):
        # copy the list of messages to simulate incoming messages.
        self.messages = messages.copy()
        self.sent = []

    async def receive_text(self):
        if self.messages:
            return self.messages.pop(0)
        await asyncio.sleep(0.1)
        return ""

    async def send_text(self, text: str):
        self.sent.append(text)

    async def close(self):
        pass

async def test_pipeline():
    """
    test the callbot pipeline using a dummy websocket.
    """
    # read sample audio file and encode in base64.
    try:
        with open("stt_test.mp3", "rb") as f:
            audio_data = f.read()
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")
    except Exception as e:
        print("error reading stt_test.mp3:", e)
        return

    # simulate a connected event.
    connected_msg = json.dumps({
        "event": "connected",
        "protocol": "Call",
        "version": "0.2.0"
    })
    # simulate a start event with a nested call sid.
    start_msg = json.dumps({
        "event": "start",
        "sequenceNumber": "1",
        "start": {
            "callSid": "DUMMY_CALL_SID",
            "streamSid": "DUMMY_STREAM_SID",
            "tracks": ["inbound"],
            "mediaFormat": {
                "encoding": "audio/x-mulaw",
                "sampleRate": 8000,
                "channels": 1
            },
            "customParameters": {
                "mediaformat": "audio/webm",
                "direction": "duplex"
            }
        },
        "streamSid": "DUMMY_STREAM_SID"
    })
    # simulate a media event with the sample audio payload.
    media_msg = json.dumps({
        "event": "media",
        "media": {"payload": audio_b64}
    })
    # simulate a stop event.
    stop_msg = json.dumps({
        "event": "stop"
    })

    messages = [connected_msg, start_msg, media_msg, stop_msg]
    dummy_ws = DummyWebsocket(messages)

    # create an agent instance.
    agent = Agent(
        name="test",
        prompt="you are a helpful agent, engage in a conversation",
        api_key=OPENAI_API_KEY,
        voice_id=DEFAULT_VOICE_ID
    )

    # create a callbot instance with dummy twilio credentials and a real webhook url.
    callbot = CallBot(
        agent=agent,
        twilio_account_sid="DUMMY_SID",
        twilio_auth_token="DUMMY_AUTH",
        twilio_number="DUMMY_NUMBER",
        webhook_url=TWILIO_WEBHOOK_URL
    )

    # run the pipeline using the dummy websocket and the dummy call sid extracted from the start event.
    print("starting pipeline...")
    await callbot.run_pipeline(dummy_ws, "DUMMY_CALL_SID")
    print("pipeline finished.")
    print("dummy websocket sent messages:", dummy_ws.sent)

async def main():
    await test_pipeline()

if __name__ == "__main__":
    asyncio.run(main())