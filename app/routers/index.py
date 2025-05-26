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





@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    Эндпоинт обрабатывает WebSocket-подключения по адресу /ws/chat
    :param websocket:
    :return:
    """
    await websocket.accept()

    try:
        while True:
            # Ожидаем сообщение от клиента
            data = await websocket.receive_text()
            data = json.loads(data)
            user_message = data["message"]
            # Получаем конфигурацию(prompt, model, temperature, frequency_penalty, presence_penalty)
            config_json = await redis_client.get(CONFIG_KEY)
            config = json.loads(config_json) if config_json else DEFAULT_CONFIG
            # В зависимости от названия модели (deepseek-chat, gpt-4, и т.п.) выбирается нужный клиент AsyncOpenAI с
            # соответствующим ключом API и base_url.
            client = get_client_for_model(config["model"])
            # Обрабатываем сообщение ИИ и возвращает ответ
            reply = await process_message(
                user_message,
                redis_client,
                config["prompt"],
                HISTORY_KEY,
                config["model"],
                client,
                config["temperature"],
                config["frequency_penalty"],
                config["presence_penalty"]
            )
            #Ответ ИИ отправляется обратно клиенту через WebSocket.
            await websocket.send_text(reply)
    #При отключении клиента (WebSocketDisconnect) происходит выход из цикла и завершение функции (без ошибки).
    except WebSocketDisconnect:
        pass





@router.post("/analyze_file")
async def analyze_file(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")

    red_client = get_redis_client()
    config_json = await red_client.get(CONFIG_KEY)
    config = json.loads(config_json) if config_json else DEFAULT_CONFIG

    model = config["model"]
    prompt = config["prompt"]
    temperature = config["temperature"]
    frequency_penalty = config["frequency_penalty"]
    presence_penalty = config["presence_penalty"]

    client = get_client_for_model(model)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Проанализируй этот файл:\n\n{content}"}
        ],
        temperature=temperature,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )

    return response.choices[0].message.content.strip()
