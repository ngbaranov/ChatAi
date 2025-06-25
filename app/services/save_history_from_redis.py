import json
from sqlalchemy.ext.asyncio import AsyncSession
from dao.dao import ChatHistoryDAO


async def save_history_from_redis(user_id: int, redis_client, session: AsyncSession):
    history_key = f"chat:{user_id}:history"
    messages = await redis_client.lrange(history_key, 0, -1)

    for item in messages:
        msg = json.loads(item)
        await ChatHistoryDAO.add(
            session,
            user_id=user_id,
            role=msg.get("role", "user"),
            message=msg.get("content", "")
        )