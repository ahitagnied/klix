import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, MagicMock
import sys
from pathlib import Path

# add the project root directory to Python path
root_dir = Path(__file__).parent.parent  # go up one level from current file
sys.path.append(str(root_dir))

from models.agent import Agent
from config import OPENAI_API_KEY

class TestAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_name = "test agent"
        self.test_prompt = "you are a test assistant"
        self.test_api_key = "test-api-key"

    def create_mock_client(self):
        mock_client = MagicMock()
        # set up your mock client expectations
        mock_assistant = MagicMock()
        mock_assistant.id = "test-assistant-id"
        mock_client.beta.assistants.create.return_value = mock_assistant

        mock_thread = MagicMock()
        mock_thread.id = "test-thread-id"
        mock_client.beta.threads.create.return_value = mock_thread

        mock_run = MagicMock()
        mock_run.status = "completed"
        mock_client.beta.threads.runs.create.return_value = mock_run
        mock_client.beta.threads.runs.retrieve.return_value = mock_run

        mock_message = MagicMock()
        mock_message.role = "assistant"
        mock_message.content = [MagicMock(text=MagicMock(value="test response"))]
        mock_messages = MagicMock()
        mock_messages.data = [mock_message]
        mock_client.beta.threads.messages.list.return_value = mock_messages

        return mock_client

    @patch("models.agent.OpenAI")  # patch where it's actually imported in agent.py
    async def test_get_response(self, mock_openai):
        mock_openai.return_value = self.create_mock_client()
        
        agent = Agent(
            name=self.test_name,
            prompt=self.test_prompt,
            api_key=self.test_api_key
        )

        try:
            response = await agent.get_response("test input")
            self.assertEqual(response, "test response")
        finally:
            await agent.close()

if __name__ == '__main__':
    unittest.main()