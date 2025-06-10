import base64
import json


from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from dotenv import load_dotenv
from jose import jwt, JWTError

from app.services.get_token import get_user_id
from app.utils.redis import get_redis_client
from app.utils.variables import CONFIG_KEY, HISTORY_KEY, DEFAULT_CONFIG
from app.services.get_ai import get_client_for_model
from app.services.gpt import process_message
from settings import settings

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

redis_client = get_redis_client()
@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/reset_chat")
async def reset_chat(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No token")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("id"))
        history_key = f"chat:{user_id}:history"
        await redis_client.delete(history_key)
        return {"status": "ok", "message": "История чата очищена"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")






@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        user_id = get_user_id(websocket)
        history_key = f"chat:{user_id}:history"
        config_key = f"chat:{user_id}:config"

        # Загружаем и отправляем историю чата
        stored = await redis_client.lrange(history_key, 0, -1)
        for item in stored:
            msg = json.loads(item)
            await websocket.send_text(json.dumps({
                "role": msg["role"],
                "content": msg["content"]
            }))

        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            user_msg = data.get("message", "")

            await websocket.send_text(json.dumps({
                "role": "user",
                "content": user_msg
            }))

            # Обработка файлов (если есть)
            if file_list := data.get("files"):
                combined_content = ""
                for file_b64 in file_list:
                    try:
                        content = base64.b64decode(file_b64).decode("utf-8")
                        combined_content += f"\n\n{content}"
                    except Exception as e:
                        combined_content += f"\n\n[Ошибка при обработке файла: {e}]"
                user_msg = f"{user_msg}:\n\n{combined_content.strip()}"

            # Получаем конфиг и вызываем process_message (он сам сохранит историю)
            cfg_json = await redis_client.get(config_key)
            config = json.loads(cfg_json) if cfg_json else DEFAULT_CONFIG
            client = get_client_for_model(config["model"])

            reply = await process_message(
                user_msg,
                redis_client,
                config["prompt"],
                history_key=history_key,
                model=config["model"],
                client=client,
                temperature=config["temperature"],
                frequency_penalty=config["frequency_penalty"],
                presence_penalty=config["presence_penalty"],
            )

            # Отправляем только ответ бота
            await websocket.send_text(json.dumps({
                "role": "assistant",
                "content": reply
            }))

    except WebSocketDisconnect:
        pass









