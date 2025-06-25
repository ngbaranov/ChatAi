from sqlalchemy.ext.asyncio import AsyncSession

from dao.dao import ChatHistoryDAO


async def get_user_sessions(user_id: int, session: AsyncSession):
    messages = await ChatHistoryDAO.get_by_user(session, user_id)

    sessions = {}
    for msg in messages:
        sessions.setdefault(msg.session_id, []).append(msg)

    return sessions