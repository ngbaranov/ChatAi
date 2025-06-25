from sqlalchemy import select, desc

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