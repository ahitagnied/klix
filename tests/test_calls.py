import os
import io
import sys
import asyncio
from pathlib import Path

# add the project root to the python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from config import DEEPGRAM_API_KEY, CARTESIA_API_KEY, OPENAI_API_KEY, DEFAULT_VOICE_ID
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.cartesia import CartesiaTTSService
from models.agent import Agent

# create an instance of the agent.
agent = Agent(
    name="test",
    prompt="you are a helpful agent, engage in a conversation",
    api_key=OPENAI_API_KEY,
    voice_id=DEFAULT_VOICE_ID
)

async def test_deepgram_stt():
    """
    test deepgram stt in isolation by invoking the service as a callable.
    """
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
    try:
        # open the audio file in binary mode
        with open("stt_test.mp3", "rb") as f:
            audio_bytes = f.read()
        # wrap the bytes in a BytesIO object and set the filename
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "stt_test.mp3"
        # call the stt service as a callable
        stt_result = await stt(audio_file)
        print("deepgram stt result:", stt_result)
    except Exception as e:
        print("error during deepgram stt test:", e)

async def test_cartesia_tts():
    """
    test cartesia tts in isolation by invoking the service as a callable.
    """
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY") or "",
        voice_id=agent.voice_id,
    )
    try:
        test_text = "hello! this is a test of the ai tts function."
        # call the tts service as a callable
        tts_result = await tts(test_text)
        # if the result is an object with a 'content' attribute, use that; otherwise, assume it's raw bytes
        audio_output = tts_result.content if hasattr(tts_result, "content") else tts_result
        output_file = "tts_test_output.wav"
        with open(output_file, "wb") as f:
            f.write(audio_output)
        print(f"tts audio written to {output_file}")
    except Exception as e:
        print("error during cartesia tts test:", e)

async def main():
    """
    run deepgram stt and cartesia tts tests.
    """
    await test_deepgram_stt()
    await test_cartesia_tts()

if __name__ == "__main__":
    asyncio.run(main())