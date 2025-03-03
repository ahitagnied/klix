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
    name='test',
    prompt='you are a helpful agent, engage in a conversation',
    api_key=OPENAI_API_KEY,
    voice_id=DEFAULT_VOICE_ID
)

async def main():
    """
    test deepgram stt and cartesia tts in isolation using process methods.
    """
    # instantiate deepgram stt and cartesia tts services
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY") or "",
        voice_id=agent.voice_id,
    )

    # test deepgram stt service
    try:
        # open the audio file in binary mode
        with open("stt_test.mp3", "rb") as f:
            mp3_bytes = f.read()
        # wrap bytes in a BytesIO object and set the filename
        audio_file = io.BytesIO(mp3_bytes)
        audio_file.name = "stt_test.mp3"
        # call the process method (assuming it accepts a file-like object)
        stt_result = await stt.process(audio_file)
        print("deepgram stt process result:", stt_result)
    except Exception as e:
        print("error during deepgram stt test:", e)

    # test cartesia tts service
    try:
        test_text = "hello! this is a test of the ai tts function."
        # call the process method (assuming it accepts a text string and returns audio bytes)
        tts_result = await tts.process(test_text)
        output_file = "tts_test_output.wav"
        with open(output_file, "wb") as f:
            f.write(tts_result)
        print(f"tts audio written to {output_file}")
    except Exception as e:
        print("error during cartesia tts test:", e)

if __name__ == "__main__":
    asyncio.run(main())