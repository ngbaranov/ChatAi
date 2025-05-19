import os
import json
from openai import OpenAI

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from dotenv import load_dotenv
import redis.asyncio as redis

from app.utils.redis import get_redis_client
from app.services.gpt import process_message

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
redis_client = get_redis_client()
DEFAULT_SYSTEM_PROMPT = "Ты дружелюбный помощник."
REDIS_HISTORY_KEY = "chat_history"
MODEL_NAME = "deepseek-chat"
# MODEL_NAME = "gpt-4.1-nano"

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            user_message = data["message"]
            system_prompt = data["prompt"]
            model = data["model"]
            temperature = data["temperature"]
            frequency_penalty = data["frequency_penalty"]
            presence_penalty = data["presence_penalty"]
            reply = await process_message(
                user_message,
                redis_client,
                system_prompt,
                REDIS_HISTORY_KEY,
                model,
                client,
                temperature,
                frequency_penalty,
                presence_penalty,
            )


            await websocket.send_text(reply)

    except WebSocketDisconnect:
        pass