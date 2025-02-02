from fastapi import FastAPI, WebSocket
from ..services.bot import CallBot
from ..models.agent import Agent

app = FastAPI()
bot = CallBot()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        audio_data = await websocket.receive_bytes()
        response = await bot.process_audio(audio_data)
        await websocket.send_bytes(response)

@app.post("/call")
async def start_call(agent: Agent, phone_number: str):
    call_sid = await bot.handle_call(agent, phone_number)
    return {"call_sid": call_sid}