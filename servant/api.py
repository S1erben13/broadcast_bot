from fastapi import FastAPI
from main import broadcast_message
from models import Message

app = FastAPI()

@app.post("/send_message")
async def send_message(message: Message):
    await broadcast_message(message)
    return {"status": "Message sent"}