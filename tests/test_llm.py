import asyncio
import os
import sys
from pathlib import Path

# add the project root to the python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from config import OPENAI_API_KEY, DEFAULT_VOICE_ID
from pipecat.services.openai import OpenAILLMService
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.pipeline.runner import PipelineRunner
from pipecat.processors.frame_processor import FrameProcessor

# define a simple user message frame class
class UserMessageFrame:
    def __init__(self, content):
        self.role = "user"
        self.content = content

# custom processor to capture the assistant reply
class CaptureAssistantReply(FrameProcessor):
    def __init__(self):
        self.name = "CaptureAssistantReply"
        self.reply = None

    async def process_frame(self, frame, direction):
        if hasattr(frame, "role") and frame.role == "assistant":
            self.reply = getattr(frame, "content", None)
            print(f"assistant replied: {self.reply}")
        return [frame]

async def test_llm_pipeline():
    # instantiate the openai llm service
    llm = OpenAILLMService(api_key=OPENAI_API_KEY, model="gpt-4o")
    
    # build a simple conversation context
    messages = [
        {"role": "system", "content": "you are a helpful assistant."}
    ]
    tools = []
    context = OpenAILLMContext(messages, tools)
    aggregator = llm.create_context_aggregator(context)
    
    # create our capture processor
    capture_processor = CaptureAssistantReply()
    
    # build a minimal pipeline: aggregator.user() -> llm -> capture_processor
    pipeline = Pipeline([
        aggregator.user(),   # converts user frame to aggregated conversation
        llm,                 # processes the conversation
        capture_processor    # capture the assistant reply
    ])
    
    # create a dummy user frame
    user_frame = UserMessageFrame("hello, how are you?")
    
    # create a pipeline task with our pipeline.
    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
    
    # override the pipeline's input stage with a dummy source that returns our user frame.
    async def dummy_source():
        return [user_frame]
    
    # since the PipelineTask object stores its pipeline in _pipeline, override that stage:
    task._pipeline.stages[0] = dummy_source
    
    # run the pipeline task
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
    
    if capture_processor.reply:
        print("test successful: assistant reply captured.")
    else:
        print("test failed: no assistant reply captured.")

if __name__ == "__main__":
    asyncio.run(test_llm_pipeline())