import asyncio
import os
import sys
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.frames.frames import TTSSpeakFrame, EndFrame, Frame, StartFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask

class AudioCollector(FrameProcessor):
    """A service to collect audio data from TTS services"""
    
    def __init__(self):
        super().__init__()
        self.audio_chunks = []
        
    async def process_frame(self, frame, direction):
        # First call the parent class implementation
        await super().process_frame(frame, direction)
        
        # Then collect any audio frames
        if hasattr(frame, 'audio') and frame.audio:
            self.audio_chunks.append(frame.audio)
            print(f"Collected audio chunk: {len(frame.audio)} bytes")
            
        # Forward the frame to the next processor
        await self.push_frame(frame, direction)
    
    def get_audio(self):
        # Combine all audio chunks
        return b''.join(self.audio_chunks)
        

async def test_cartesia_tts():
    # Retrieve your Cartesia API key from environment or hardcode for testing
    cartesia_api_key = os.getenv("CARTESIA_API_KEY", "your-cartesia-api-key")
    
    # Use your preferred voice id (default provided here)
    voice_id = "79a125e8-cd45-4c13-8a67-188112f4dd22"
    
    # Initialize the Cartesia TTS service
    tts_service = CartesiaTTSService(
        api_key=cartesia_api_key,
        voice_id=voice_id
    )
    
    # Create an audio collector to capture the output
    collector = AudioCollector()
    
    # Create a pipeline with the TTS service and collector
    pipeline = Pipeline([tts_service, collector])
    
    # Create a pipeline task
    task = PipelineTask(pipeline)
    
    # Create a pipeline runner
    runner = PipelineRunner()
    
    # The text to convert to speech
    text = "hello, this is testing cartesia"
    
    print("Starting TTS pipeline...")
    
    try:
        # Queue frames to the pipeline
        await task.queue_frames([
            TTSSpeakFrame(text),
            EndFrame()
        ])
        
        # Run the pipeline with a timeout (set to 60 seconds here)
        try:
            await asyncio.wait_for(runner.run(task), timeout=60)
        except asyncio.TimeoutError:
            print("TTS pipeline timed out after 60 seconds. Cancelling task.")
            await runner.cancel(task)
        
        # Get the collected audio
        audio_data = collector.get_audio()
        
        # Save the audio data to a file if we got any
        if audio_data:
            try: 
                output_filename = "cartesia_test_output.wav"
                # Save using an absolute path (optional, for clarity)
                abs_path = os.path.abspath(output_filename)
                with open(abs_path, "wb") as f:
                    f.write(audio_data)
                print(f"Audio saved to {abs_path}")
            except Exception as e:
                print(f"Error saving audio data: {e}")
        else:
            print("No audio data was generated")
    except Exception as e:
        print(f"Error in TTS pipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cartesia_tts())