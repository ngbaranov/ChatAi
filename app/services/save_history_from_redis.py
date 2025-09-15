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

        # Ограничиваем количество сессий до 10 для каждого пользователя
        await _cleanup_old_sessions(db, user_id, sessions_limit=10)

        # await redis_client.delete(history_key)
        print(f"🧹 Redis очищен: {history_key}")


async def _cleanup_old_sessions(db: AsyncSession, user_id: int, sessions_limit: int = 10):
    """Удаляет старые сессии для конкретного пользователя, оставляя только последние sessions_limit сессий"""

    # Получаем все сессии пользователя, отсортированные по времени создания (самые новые первыми)
    sessions_query = select(
        ChatHistory.session_id,
        func.min(ChatHistory.timestamp).label("start_time")
    ).where(
        ChatHistory.user_id == user_id
    ).group_by(
        ChatHistory.session_id
    ).order_by(
        func.min(ChatHistory.timestamp).desc()
    )

    result = await db.execute(sessions_query)
    sessions = result.fetchall()

    if len(sessions) <= sessions_limit:
        print(f"📊 У пользователя {user_id} всего {len(sessions)} сессий, лимит: {sessions_limit} — очистка не нужна")
        return 0

    # Получаем session_id сессий, которые нужно удалить (все кроме последних sessions_limit)
    sessions_to_delete = [session.session_id for session in sessions[sessions_limit:]]

    if sessions_to_delete:
        # Удаляем все сообщения из старых сессий
        delete_stmt = delete(ChatHistory).where(
            ChatHistory.user_id == user_id,
            ChatHistory.session_id.in_(sessions_to_delete)
        )
        await db.execute(delete_stmt)
        await db.commit()
        print(f"🧹 Удалено {len(sessions_to_delete)} старых сессий пользователя {user_id}")
        return len(sessions_to_delete)

    return 0


async def _cleanup_old_records(db: AsyncSession, limit: int = 20):
    """Удаляет старые записи, оставляя только последние limit записей (устаревшая функция)"""

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
