from sqlalchemy import select, desc, func

from dao.base import BaseDAO
from auth.model import User
from app.models.chat_history import ChatHistory


class UserDAO(BaseDAO):
    model = User


class ChatHistoryDAO(BaseDAO):
    model = ChatHistory

    @classmethod
    async def get_by_user(cls, session, user_id: int):
        stmt = (
            select(cls.model)
            .where(cls.model.user_id == user_id)
            .order_by(desc(cls.model.timestamp))
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def get_sessions_summary(cls, session, user_id: int):
        # Подзапрос: earliest message in each session
        subquery = (
            select(
                cls.model.session_id,
                func.min(cls.model.timestamp).label("start_time")
            )
            .where(cls.model.user_id == user_id)
            .group_by(cls.model.session_id)
            .subquery()
        )

        # Основной запрос: выбираем session_id, start_time и preview
        stmt = (
            select(
                cls.model.session_id,
                subquery.c.start_time,
                cls.model.message
            )
            .join(subquery, cls.model.session_id == subquery.c.session_id)
            .where(cls.model.timestamp == subquery.c.start_time)
            .order_by(subquery.c.start_time.desc())
        )

        result = await session.execute(stmt)
        return [(row.session_id, row.start_time, row.message[:50]) for row in result]

    @staticmethod
    async def get_last_session(user_id: int, session):
        # Получаем последний session_id по времени
        subq = (
            select(
                ChatHistory.session_id,
                func.min(ChatHistory.timestamp).label("start_time")
            )
            .where(ChatHistory.user_id == user_id)
            .group_by(ChatHistory.session_id)
            .order_by(desc("start_time"))
            .limit(1)
        ).subquery()

        # Получаем все сообщения из этой сессии
        stmt = (
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .where(ChatHistory.session_id == subq.c.session_id)
            .order_by(ChatHistory.timestamp)
        )
        result = await session.execute(stmt)
        return result.scalars().all()