import os
import json
from openai import OpenAI

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from dotenv import load_dotenv
import redis.asyncio as redis

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
redis_client = redis.from_url(os.getenv("REDIS_URL"))

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

REDIS_HISTORY_KEY = "chat_history"
DEFAULT_SYSTEM_PROMPT = "Ты дружелюбный помощник."# Ключ для хранения истории сообщений в RedisR

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            user_message = await websocket.receive_text()

            history_json = await redis_client.get(REDIS_HISTORY_KEY)
            history = json.loads(history_json) if history_json else []
            history.insert(0, {"role": "system", "content": DEFAULT_SYSTEM_PROMPT})
            history.append({"role": "user", "content": user_message})

            response = client.chat.completions.create(
                model="gpt-4",
                messages=history
            )
            reply = response.choices[0].message.content.strip()
            history.append({"role": "assistant", "content": reply})

            await redis_client.set(REDIS_HISTORY_KEY, json.dumps(history[1:]))
            await websocket.send_text(reply)

    except WebSocketDisconnect:
        pass