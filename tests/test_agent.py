import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, MagicMock
import sys
from pathlib import Path
import os

# add the project root directory to Python path
root_dir = Path(__file__).parent.parent  # go up one level from current file
sys.path.append(str(root_dir))

from models.agent import Agent
from config import OPENAI_API_KEY

class TestAgentRealResponse(unittest.IsolatedAsyncioTestCase):
    """
    this test calls the actual open api (not mocked).
    make sure you have a valid OPENAI_API_KEY set in your environment.
    """

    def setUp(self):
        # provide default values or rely on environment vars
        self.test_name = "real test agent"
        self.test_prompt = (
            "you are a helpful ai assistant. "
            "answer questions to the best of your ability."
        )
        # if OPENAI_API_KEY isn't in your env, just hard-code or pass it here
        self.test_api_key = os.getenv("OPENAI_API_KEY")

        if not self.test_api_key:
            raise ValueError("no openai api key found. please set OPENAI_API_KEY in your environment.")

    async def asyncTearDown(self):
        # if you do any post-test cleanup, put it here
        pass

    async def test_get_real_response(self):
        """
        calls the real openai api, gets a response, and prints it. this is an integration test.
        """
        # create the real agent (no patching)
        agent = Agent(
            name=self.test_name,
            prompt=self.test_prompt,
            api_key=self.test_api_key
        )

        # example user message
        user_input = "write a haiku"
        response = await agent.get_response(user_input)

        # print out both sides to see them in the console
        print(f"\n[TEST] user input: {user_input}")
        print(f"[TEST] assistant (real) response:\n{response}")

        # basic assertion: we got *something* back
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

        # clean up the assistant + thread
        await agent.close()

if __name__ == "__main__":
    unittest.main()