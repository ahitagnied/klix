# klix

This project aims to build a system for evaluating the performance of AI voice agents.  It allows for real-time interaction with an agent via a phone call, transcribes the conversation, and provides feedback based on predefined criteria. This is inspired by the need for faster bug detection and performance analysis in AI voice agents, similar to the approach taken by Fixa (YC F24).

## Features

*   **Real-time audio transcription and translation:** Uses OpenAI's Whisper API to convert audio from a phone call into text in real-time.
*   **AI-powered agent interaction:** Integrates with OpenAI's Assistants API to create conversational AI agents that respond to user input.
*   **Text-to-speech synthesis:**  Uses OpenAI's TTS API to convert agent responses back into audio for playback to the caller.
*   **Twilio integration:** Enables initiating and managing phone calls for agent interaction.
*   **Websocket communication:** Facilitates real-time audio streaming between the client (phone call) and the server.
*   **Conversation evaluation:** Provides a framework for evaluating conversations based on custom criteria (using OpenAI's Chat Completions API).
*   **Comprehensive testing:** Includes unit and integration tests to ensure code quality and functionality.


## Usage

The system consists of a FastAPI server that handles websocket connections for audio streaming and a Twilio integration for initiating calls.  To use the system:

1.  **Set up environment variables:** Create a `.env` file with your OpenAI API key, Twilio Account SID, Auth Token, and Twilio phone number:

    ```
    OPENAI_API_KEY=your_openai_api_key
    TWILIO_ACCOUNT_SID=your_twilio_account_sid
    TWILIO_AUTH_TOKEN=your_twilio_auth_token
    YOUR_TWILIO_NUMBER=+1your_twilio_number
    ```

2.  **Run the server:** Start the FastAPI server using `uvicorn main:app --reload`.

3.  **Initiate a call:** Send a POST request to `/call` with the agent details and the phone number to call.  The response will contain the call SID.

    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"name": "burger_bot", "prompt": "You are a helpful burger shop assistant.", "phone_number": "+15551234567"}' http://localhost:8765/call
    ```


## Installation

1.  Clone the repository: `git clone git@github.com:your_username/klix.git`
2.  Create a virtual environment: `python3 -m venv venv`
3.  Activate the virtual environment: `source venv/bin/activate`
4.  Install dependencies: `pip install -r requirements.txt`

## Technologies Used

*   **Python:** The primary programming language for the project.
*   **FastAPI:**  A modern, high-performance web framework for building the API.
*   **Uvicorn:** An ASGI server implementation for running the FastAPI application.
*   **OpenAI API:**  Used for various functionalities, including:
    *   **Whisper API:** For real-time audio transcription.
    *   **Assistants API:** For creating and interacting with conversational AI agents.
    *   **TTS API:** For text-to-speech conversion.
    *   **Chat Completions API:** For evaluating conversations.
*   **Twilio API:** For managing phone calls and handling real-time audio streaming.
*   **Websockets:**  Used for real-time bidirectional communication between the client and server.
*   **Dataclasses:**  For creating simple and efficient data structures in Python.
*   **pytest:**  For writing and running unit and integration tests.


## Configuration

The application's configuration is managed through the `config.py` file, which loads environment variables and defines default settings.  Important settings include API keys, server port, and voice ID.


## API Documentation

**POST /call:**

*   **Request:**
    ```json
    {
      "name": "agent_name",
      "prompt": "agent_system_prompt",
      "phone_number": "+15551234567"
    }
    ```

*   **Response:**
    ```json
    {
      "call_sid": "CLxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
    ```

**WebSocket **/ws**:  Handles real-time audio streaming.  The communication protocol is JSON, with events like `start`, `media`, and `stop`.

## Dependencies

The project's dependencies are listed in the `requirements.txt` file.  Install them using `pip install -r requirements.txt`.


## Contributing

Contributions are welcome!  Please open issues or submit pull requests.


## Testing

Unit and integration tests are located in the `tests` directory.  Run tests using `pytest`.
