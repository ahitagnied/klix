from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# load environment variables from .env early
load_dotenv()

# add the project root directory to python path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir.parent))

# import your callbot and agent classes
from services.bot import CallBot
from models.agent import Agent
from config import TWILIO_ACCOUNT_SID, OPENAI_API_KEY, TWILIO_AUTH_TOKEN, TWILIO_WEBHOOK_URL, YOUR_TWILIO_NUMBER


# get twilio and webhook configuration from environment variables.
twilio_account_sid = TWILIO_ACCOUNT_SID
twilio_auth_token = TWILIO_AUTH_TOKEN
twilio_number = YOUR_TWILIO_NUMBER
# this should be your publicly accessible url for twilio to reach your stream endpoint.
webhook_url = TWILIO_WEBHOOK_URL 
# create fastapi instance
app = FastAPI()

# instantiate your agent with the required parameters.
# make sure your .env has openai api key set.
agent = Agent(
    name="ai agent",
    prompt="you are a helpful ai assistant. answer questions to the best of your ability.",
    api_key=OPENAI_API_KEY
)

# instantiate your callbot with the agent and twilio configuration.
bot = CallBot(
    agent=agent,
    twilio_account_sid=twilio_account_sid,
    twilio_auth_token=twilio_auth_token,
    twilio_number=twilio_number,
    webhook_url=webhook_url
)

# websocket endpoint that twilio will connect to for real-time audio streaming.
@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    websocket endpoint that accepts connection and delegates handling to callbot.
    """
    await websocket.accept()
    try:
        # delegate handling of the websocket connection to callbot.
        await bot.handle_websocket(websocket, path="/ws/stream")
    except WebSocketDisconnect:
        print("websocket disconnected")
    except Exception as e:
        print(f"error in websocket endpoint: {e}")

# http endpoint to initiate an outbound call.
# call this endpoint (e.g., via a post request) with a phone number.
@app.post("/call")
async def start_call(phone_number: str):
    """
    initiate an outbound call using callbot.
    """
    call_sid = await bot.make_call(phone_number)
    if call_sid:
        return {"call_sid": call_sid}
    else:
        return {"error": "failed to initiate call"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)