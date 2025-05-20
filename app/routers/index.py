import os
import json
from openai import AsyncOpenAI

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Body, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from dotenv import load_dotenv
import redis.asyncio as redis

from app.utils.redis import get_redis_client
from app.services.gpt import process_message

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

redis_client = get_redis_client()

CONFIG_KEY = "global_ai_config"
HISTORY_KEY = "chat_history"

DEFAULT_CONFIG = {
    "prompt": "Ты дружелюбный помощник.",
    "model": "deepseek-chat",
    "temperature": 0.2,
    "frequency_penalty": 0.1,
    "presence_penalty": 0.2
}


def get_client_for_model(model_name: str) -> AsyncOpenAI:
    if model_name.startswith("deepseek"):
        return AsyncOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
    else:
        return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/set_config")
async def set_config(data: dict = Body(...)):
    await redis_client.set(CONFIG_KEY, json.dumps(data))
    return {"status": "ok", "message": "Настройки обновлены"}


@router.get("/get_config")
async def get_config():
    config_json = await redis_client.get(CONFIG_KEY)
    if config_json:
        return json.loads(config_json)
    return DEFAULT_CONFIG


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            user_message = data["message"]

            config_json = await redis_client.get(CONFIG_KEY)
            config = json.loads(config_json) if config_json else DEFAULT_CONFIG

            client = get_client_for_model(config["model"])

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
            await websocket.send_text(reply)

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
