from dataclasses import dataclass
from typing import Optional
import sys
from pathlib import Path

# add the project root to the Python path
root_dir = Path(__file__).parent.parent  # go up one level from current file
sys.path.append(str(root_dir))

from config import DEFAULT_VOICE_ID
from openai import OpenAI
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

@dataclass
class Agent:
    """
    initializes an agent with a name, scenario through prompt attribute and a voice id.

    attributes:
        name (str): the name of the agent.
        prompt (str): the system prompt/instructions for the agent.
        voice_id (str): the voice id for the agent. defaults to default_voice_id.
        api_key (str): openai api key. if not provided, will try to get from config or environment.
    """
    name: str
    prompt: str
    voice_id: str = DEFAULT_VOICE_ID
    api_key: Optional[str] = None

    def __post_init__(self):
        """
        initialize openai client and create assistant and thread.
        """
        # get api key from parameter, config, or environment
        self.api_key = self.api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("openai api key not found. please provide it as a parameter, in config.py, or set OPENAI_API_KEY environment variable.")

        # initialize client with api key
        self.client = OpenAI(api_key=self.api_key)
        
        # create an assistant with the provided prompt
        self.assistant = self.client.beta.assistants.create(
            instructions=self.prompt,
            name=self.name,
            model="gpt-4-turbo-preview"
        )
        
        # store assistant id
        self.assistant_id = self.assistant.id
        if not self.assistant_id:
            raise ValueError("assistant id could not be initialized.")

        # create a thread for the conversation
        self.thread = self.client.beta.threads.create()
        self.thread_id = self.thread.id
        if not self.thread_id:
            raise ValueError("thread id could not be initialized.")

    async def get_response(self, user_input: str) -> str:
        """
        get a response from the agent based on the user input.

        args:
            user_input (str): the user's message.

        returns:
            str: the assistant's response.
        """
        try:
            # add message to thread
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=user_input
            )

            # create a run
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )

            # wait for the run to complete
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    raise Exception(f"run failed with status: {run_status.status}")
                await asyncio.sleep(0.5)

            # get the latest message
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread_id
            )
            
            # return the assistant's response
            for message in messages.data:
                if message.role == "assistant":
                    return message.content[0].text.value

            return "no response received"

        except Exception as e:
            return f"error getting response: {str(e)}"

    async def close(self):
        """
        clean up resources by deleting the assistant and thread.
        """
        try:
            if hasattr(self, 'assistant_id'):
                self.client.beta.assistants.delete(self.assistant_id)
            if hasattr(self, 'thread_id'):
                self.client.beta.threads.delete(self.thread_id)
        except Exception as e:
            print(f"error during cleanup: {str(e)}")