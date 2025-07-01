import json
from uuid import uuid4
from sqlalchemy import insert
from app.models.chat_history import ChatHistory
from redis.asyncio.lock import Lock
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.redis import get_redis_client

redis_client = get_redis_client()


async def save_history_from_redis(user_id: int, db: AsyncSession):
    loaded_flag = f"chat:{user_id}:__LOADED_FROM_DB__"
    if await redis_client.exists(loaded_flag):
        print(f"⚠️ История уже была загружена из БД — пропускаем сохранение")
        await redis_client.delete(loaded_flag)
        return
    history_key = f"chat:{user_id}:history"
    lock = Lock(redis_client, name=f"lock:{user_id}", timeout=10)

    async with lock:
        stored = await redis_client.lrange(history_key, 0, -1)

        if not stored:
            print(f"ℹ️ Redis пуст для user_id={user_id}, нечего сохранять.")
            return

        session_id = uuid4().hex

        messages = [
            {
                "user_id": user_id,
                "message": msg["content"],
                "role": msg["role"],
                "session_id": session_id
            }
            for msg in map(json.loads, stored)
        ]

        await db.execute(insert(ChatHistory), messages)
        await db.commit()
        print(f"✅ Сохранено {len(messages)} сообщений в БД (user_id={user_id})")

        # await redis_client.delete(history_key)
        print(f"🧹 Redis очищен: {history_key}")
