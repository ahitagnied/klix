import asyncio
import os
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_VOICE_ID = "your_default_voice_id"  # if needed

# Get the absolute path to your project root
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from models.agent import Agent 
from dotenv import load_dotenv

load_dotenv()
print("Project root:", PROJECT_ROOT)
print("Python path:", sys.path)
print("Loaded API Key:", os.getenv("OPENAI_API_KEY"))

async def main():
    # create an agent instance with a name and a prompt
    agent = Agent(
        name="Test Agent",
        prompt="You are a helpful assistant. How can I assist you today?"
    )
    
    # define a sample user input
    user_input = "Hello, can you tell me a joke?"
    
    try:
        response = await agent.get_response(user_input)
        print("Assistant Response:", response)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    asyncio.run(main())