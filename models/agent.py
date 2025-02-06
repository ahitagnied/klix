from dataclasses import dataclass
from typing import Optional
from config import DEFAULT_VOICE_ID
from openai import OpenAI
from config import DEFAULT_VOICE_ID, OPENAI_API_KEY, OPENAI_PROJECT_ID
from dotenv import load_dotenv
import asyncio
from pathlib import Path

load_dotenv()

@dataclass
class Agent:
    """
    initialises an agent with a name, scenario through prompt attribute and a voice id through the voice_id attribute

    attributes: 
        name (str): a string representing the name of the agent.
        prompt (str): a string representing the prompt for the agent.
        voice_id (str): a string representing the voice id of the agent. defaults to DEFAULT_VOICE_ID.
    """
    name: str
    prompt: str
    voice_id: str = DEFAULT_VOICE_ID

    def __post_init__(self):
        """
        initialise an open ai agent client that the call bot will call
        """
        # initialize client based on api key type
        if OPENAI_API_KEY.startswith('sk-proj-'):
            self.client = OpenAI(
                api_key=OPENAI_API_KEY,
                organization=OPENAI_PROJECT_ID  # required for project api keys
            )
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)

        # create an assistant
        self.assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.prompt,
            model="gpt-4-turbo",
        )

        print(f"assistant created: id = {self.assistant.id}")  # debugging line

        # get assistant 
        self.assistant_id = getattr(self.assistant, 'id', None)
        if self.assistant_id is None and isinstance(self.assistant, dict):
            self.assistant_id = self.assistant.get("id")
        if self.assistant_id is None:
            raise ValueError("Assistant ID could not be initialized.")

        # create a thread to represents a conversation between a user and the assistant
        self.thread = self.client.beta.threads.create()

        # save the thread id in a dedicated attribute 
        self.thread_id = getattr(self.thread, 'id', None)
        if self.thread_id is None and isinstance(self.thread, dict):
            self.thread_id = self.thread.get("id")
        if self.thread_id is None:
            raise ValueError("Thread ID could not be initialized.")

    async def get_response(self, user_input: str) -> str:
        """
        get a response from the defined agent based on the user input

        arguments: 
            user_input (str): the user input

        returns:
            resposne (str): the response of the assistant to the user input
        """
        # add a message to the thread
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=user_input
        )

        # request a reply from the assistant
        response = await self.client.beta.assistants.reply(
            assistant_id=self.assistant.id,
            thread_id=self.thread_id
        )

        # return the reply
        return response.content