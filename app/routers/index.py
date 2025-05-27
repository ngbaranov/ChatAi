import base64
import os
import json
from openai import AsyncOpenAI

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Body, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from dotenv import load_dotenv
import redis.asyncio as redis

from app.utils.redis import get_redis_client
from app.utils.settings import CONFIG_KEY, HISTORY_KEY, DEFAULT_CONFIG
from app.services.get_ai import get_client_for_model
from app.services.gpt import process_message

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

redis_client = get_redis_client()
@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/reset_chat")
async def reset_chat():
    """
    Удаляет из Redis ключ с историей чата.
    """
    await redis_client.delete(HISTORY_KEY)
    return {"status": "ok", "message": "История чата очищена"}





@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            # Основное сообщение (инструкция или обычный чат)
            user_msg = data.get("message", "")

            # Если пришёл файл — декодируем и добавляем к запросу
            if file_b64 := data.get("file"):
                content = base64.b64decode(file_b64).decode("utf-8")
                # Объединяем инструкцию и содержимое файла
                user_msg = f"{user_msg}:\n\n{content}"

            # Берём глобальные настройки из Redis
            cfg_json = await redis_client.get(CONFIG_KEY)
            config = json.loads(cfg_json) if cfg_json else DEFAULT_CONFIG

            # Инициализируем нужный клиент
            client = get_client_for_model(config["model"])

            # Обрабатываем через ту же логику process_message
            reply = await process_message(
                user_msg,
                redis_client,
                config["prompt"],
                history_key=HISTORY_KEY,
                model=config["model"],
                client=client,
                temperature=config["temperature"],
                frequency_penalty=config["frequency_penalty"],
                presence_penalty=config["presence_penalty"],
            )

            await websocket.send_text(reply)

    except WebSocketDisconnect:
        pass









