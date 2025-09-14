import json
from uuid import uuid4
from sqlalchemy import insert, select, func, delete
from app.models.chat_history import ChatHistory
from redis.asyncio.lock import Lock
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.redis import get_redis_client

redis_client = get_redis_client()


async def save_history_from_redis(user_id: int, db: AsyncSession, limit: int = 200):
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

        await _cleanup_old_records(db, limit)

        # await redis_client.delete(history_key)
        print(f"🧹 Redis очищен: {history_key}")


async def _cleanup_old_records(db: AsyncSession, limit: int = 20):
    """Удаляет старые записи, оставляя только последние limit записей"""

    # Подсчитываем общее количество записей
    count_query = select(func.count(ChatHistory.id))
    result = await db.execute(count_query)
    total_count = result.scalar()

    if total_count <= limit:
        print(f"📊 Всего записей: {total_count}, лимит: {limit} — очистка не нужна")
        return 0

    records_to_delete = total_count - limit
    print(f"📊 Всего записей: {total_count}, нужно удалить: {records_to_delete}")

    # Получаем ID самых старых записей для удаления
    oldest_ids_query = select(ChatHistory.id).order_by(
        ChatHistory.timestamp
    ).limit(records_to_delete)

    oldest_ids_result = await db.execute(oldest_ids_query)
    oldest_ids = [row[0] for row in oldest_ids_result.fetchall()]

    if oldest_ids:
        # Удаляем старые записи
        delete_stmt = delete(ChatHistory).where(
            ChatHistory.id.in_(oldest_ids)
        )
        await db.execute(delete_stmt)
        await db.commit()
        print(f"🧹 Удалено {len(oldest_ids)} старых записей из истории чата")
        return len(oldest_ids)

    return 0
