"""
this file contains tests for the callbot class. it uses a mock websocket class
to simulate the behavior of a real websocket, and we also mock out openai
audio transcription and speech endpoints.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import json
import base64
import sys
import websockets

# add the project root to the python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from services.bot import CallBot
from models.agent import Agent

# mock audio data in base64 for testing
SAMPLE_AUDIO = base64.b64encode(b"mock_audio_data").decode('utf-8')
SAMPLE_TEXT = "hello, this is a test message"

class MockWebSocket:
    """
    a mock websocket class that simulates the recv() and send() methods.
    this allows us to test the handle_websocket method in callbot.
    """
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self._message_queue = []

    async def send(self, message: str):
        """
        simulate sending a message out via websocket.
        """
        self.sent_messages.append(message)

    def add_message(self, message: dict):
        """
        queue a message (as json) that will be returned by recv().
        """
        self._message_queue.append(json.dumps(message))

    async def recv(self) -> str:
        """
        simulate websocket.recv() by popping from the queued messages.
        if there are no messages left, simulate a closed connection.
        """
        if not self._message_queue:
            raise websockets.exceptions.ConnectionClosedOK(1000, "no more messages")
        return self._message_queue.pop(0)

    async def close(self):
        """
        simulate closing the websocket.
        """
        self.closed = True

@pytest.fixture
def mock_agent():
    """
    create a mock agent that simulates the openai calls (transcription, speech).
    """
    mock = Mock()
    mock.get_response = AsyncMock(return_value="this is a test response")
    mock.voice_id = "test_voice"

    # mock the openai client object
    mock.client = Mock()
    mock.client.audio = Mock()
    mock.client.audio.speech = Mock()
    mock.client.audio.transcriptions = Mock()

    # mock the agent's close
    mock.close = AsyncMock()

    return mock

@pytest.fixture
def callbot(mock_agent):
    """
    create a callbot instance using the mock agent and fake twilio credentials.
    """
    return CallBot(
        agent=mock_agent,
        twilio_account_sid="test_sid",
        twilio_auth_token="test_token",
        twilio_number="+1234567890",
        webhook_url="ws://localhost:8000"
    )

@pytest.mark.asyncio
async def test_make_call(callbot):
    """
    test making a call via twilio by mocking calls.create().
    """
    with patch.object(callbot.twilio_client.calls, 'create') as mock_create:
        mock_create.return_value = Mock(sid='test_call_sid')
        call_sid = await callbot.make_call("+1987654321")
        assert call_sid == 'test_call_sid'
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_handle_websocket(callbot):
    """
    test websocket handling with mock audio data. we verify both the agent
    methods are called and that a reply was sent back through the websocket.
    """
    mock_websocket = MockWebSocket()

    # mock the audio conversion methods in the callbot
    callbot._convert_audio_to_text = AsyncMock(return_value=SAMPLE_TEXT)
    callbot._convert_text_to_audio = AsyncMock(return_value=base64.b64decode(SAMPLE_AUDIO))

    # enqueue messages: start, media, and stop
    mock_websocket.add_message({'event': 'start', 'call_sid': 'test_call_sid'})
    mock_websocket.add_message({'event': 'media', 'media': {'payload': SAMPLE_AUDIO}})
    mock_websocket.add_message({'event': 'stop'})

    # run the websocket handler
    await callbot.handle_websocket(mock_websocket, '/stream')

    # confirm something was sent back to the caller
    assert len(mock_websocket.sent_messages) > 0, "no response was sent back through the websocket"

    # parse the last message that was sent
    last_sent_str = mock_websocket.sent_messages[-1]
    last_sent = json.loads(last_sent_str)

    # confirm the bot replied with 'media' event containing audio payload
    assert last_sent["event"] == "media"
    assert "media" in last_sent
    assert "payload" in last_sent["media"]

    # verify the agent was called with the recognized text
    callbot.agent.get_response.assert_awaited_once_with(SAMPLE_TEXT)

    # verify that text-to-audio was called with the agent's response
    callbot._convert_text_to_audio.assert_awaited_once_with("this is a test response")

@pytest.mark.asyncio
async def test_audio_conversion(callbot):
    """
    test audio conversion methods by mocking the openai audio endpoints.
    """
    # mock text-to-speech response
    mock_speech_response = Mock()
    mock_speech_response.content = base64.b64decode(SAMPLE_AUDIO)

    callbot.agent.client.audio.speech.create = AsyncMock(return_value=mock_speech_response)
    audio = await callbot._convert_text_to_audio(SAMPLE_TEXT)
    assert isinstance(audio, bytes)
    assert audio == base64.b64decode(SAMPLE_AUDIO)

    # mock speech-to-text (transcription) response
    mock_transcription_response = Mock()
    mock_transcription_response.text = SAMPLE_TEXT

    callbot.agent.client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription_response)
    text = await callbot._convert_audio_to_text(base64.b64decode(SAMPLE_AUDIO))
    assert text == SAMPLE_TEXT

@pytest.mark.asyncio
async def test_cleanup(callbot):
    """
    test cleanup and resource management. ensures calls are ended and the
    agent is closed.
    """
    callbot.active_calls['test_call_sid'] = {'websocket': MockWebSocket()}

    # create a mock for the twilio call and patch the calls(...) usage
    mock_call = Mock()
    mock_call.update = Mock()

    with patch.object(callbot.twilio_client.calls, '__call__', return_value=mock_call):
        await callbot.close()

        # confirm the call was ended
        mock_call.update.assert_called_once_with(status="completed")

        # confirm the active calls dict was cleared
        assert len(callbot.active_calls) == 0

if __name__ == "__main__":
    import pytest
    pytest.main(["-v", __file__])