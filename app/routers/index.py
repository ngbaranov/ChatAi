import base64
import json

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from dotenv import load_dotenv
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.save_history_from_redis import save_history_from_redis
from app.utils.redis import get_redis_client
from app.utils.variables import CONFIG_KEY, DEFAULT_CONFIG
from app.services.get_ai import get_client_for_model
from app.services.gpt import process_message
from dao.dao import ChatHistoryDAO
from database.db_depends import get_db
from settings import settings

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

redis_client = get_redis_client()
@router.get("/", response_class=HTMLResponse)
async def root(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return templates.TemplateResponse("index.html", {"request": request, "sessions": []})

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("id"))
    except JWTError:
        return templates.TemplateResponse("index.html", {"request": request, "sessions": []})

    sessions = await ChatHistoryDAO.get_sessions_summary(db, user_id)
    return templates.TemplateResponse("index.html", {"request": request, "sessions": sessions})

@router.post("/reset_chat")
async def reset_chat(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No token")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("id"))

        # Сохраняем текущую историю в БД перед очисткой
        await save_history_from_redis(user_id, db, limit=200)

        history_key = f"chat:{user_id}:history"
        await redis_client.delete(history_key)
        return {"status": "ok", "message": "История чата очищена"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    print("🔌 WebSocket открыт")

    user_id = None  # Инициализируем переменную

    try:
        token = websocket.cookies.get("access_token")
        if not token:
            await websocket.close()
            print("❌ WebSocket закрыт — токен отсутствует")
            return

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = int(payload.get("id"))
        except JWTError:
            await websocket.close()
            print("❌ WebSocket закрыт — токен недействителен")
            return

        print(f"👤 user_id: {user_id}")
        history_key = f"chat:{user_id}:history"

        # 📦 Отправляем историю
        stored = await redis_client.lrange(history_key, 0, -1)
        parsed_history = [json.loads(i) for i in stored]
        await websocket.send_text(json.dumps({"history": parsed_history}))
        print("📤 История отправлена")

        while True:
            data = await websocket.receive_text()
            print(f"📨 Получено: {data}")
            parsed_data = json.loads(data)

            if parsed_data.get("message") == "__reset__":
                await redis_client.delete(history_key)
                await websocket.send_text(json.dumps({"history": []}))
                print("🧹 История очищена")
                continue

            user_msg = parsed_data.get("message")

            if "files" in parsed_data and parsed_data["files"]:
                files_text = await process_files(parsed_data["files"])
                user_msg += f"\n\n[Вложенные файлы:]\n{files_text}"

            # ⚙️ Загружаем конфиг пользователя
            config_data = await redis_client.hgetall(f"{CONFIG_KEY}:{user_id}") or DEFAULT_CONFIG
            system_prompt = config_data.get("prompt", DEFAULT_CONFIG["prompt"])
            model = config_data.get("model", DEFAULT_CONFIG["model"])
            temperature = float(config_data.get("temperature", DEFAULT_CONFIG["temperature"]))
            frequency_penalty = float(config_data.get("frequency_penalty", DEFAULT_CONFIG["frequency_penalty"]))
            presence_penalty = float(config_data.get("presence_penalty", DEFAULT_CONFIG["presence_penalty"]))

            # 🤖 Получаем клиента по модели
            client = get_client_for_model(model)

            # 🧠 Обработка сообщения
            reply = await process_message(
                user_id=user_id,
                user_message=user_msg,
                redis_client=redis_client,
                system_prompt=system_prompt,
                history_key=history_key,
                model=model,
                client=client,
                temperature=temperature,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )

            # 📤 Отправляем ответ клиенту
            await websocket.send_text(json.dumps({"role": "assistant", "content": reply}))

    except WebSocketDisconnect:
        print("❌ Отключение WebSocket")
        if user_id:  # Проверяем, что user_id определен
            try:
                await save_history_from_redis(user_id, db, limit=10)
            except Exception as e:
                print(f"❌ Ошибка при сохранении истории: {e}")

    except Exception as e:
        print(f"❌ Ошибка WebSocket: {e}")
        try:
            await websocket.close()
        except Exception:
            print("⚠️ WebSocket уже был закрыт")





async def process_files(file_list):
    """Обработка вложенных файлов"""
    combined = []
    for file_b64 in file_list:
        try:
            content = base64.b64decode(file_b64).decode("utf-8")
            combined.append(content)
        except Exception as e:
            combined.append(f"[Ошибка файла: {e}]")
    return "\n\n".join(combined)





@router.get("/load_session")
async def load_session(request: Request, session_id: str, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401)

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("id"))
    except JWTError:
        raise HTTPException(401)

    history_key = f"chat:{user_id}:history"
    messages = await ChatHistoryDAO.get_by_session(db, user_id, session_id)

    # загружаем в Redis
    await redis_client.delete(history_key)
    for msg in messages:
        await redis_client.rpush(history_key, json.dumps({
            "role": msg.role,
            "content": msg.message
        }))
    await redis_client.set(f"chat:{user_id}:__LOADED_FROM_DB__", "1", ex=3600)
    print(f"🚩 Установлен флаг LOADED_FROM_DB для user_id={user_id}")
    return {"status": "ok"}

@router.get("/api/sessions")
async def get_sessions(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return {"sessions": []}

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("id"))
    except JWTError:
        return {"sessions": []}

    sessions = await ChatHistoryDAO.get_sessions_summary(db, user_id)
    return {"sessions": sessions}
