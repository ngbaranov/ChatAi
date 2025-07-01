from sqlalchemy import select, and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


class BaseDAO:
    model = None
    @classmethod
    async def add(cls, session: AsyncSession, **values):
        # Добавить одну запись
        new_instance = cls.model(**values)
        session.add(new_instance)
        try:
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        return new_instance

    @classmethod
    async def get_by_field(cls, session: AsyncSession, **filters):
        """Получить запись по одному или нескольким полям."""
        if not filters:
            raise ValueError("Необходимо указать хотя бы одно поле для поиска.")

        conditions = [getattr(cls.model, key) == value for key, value in filters.items()]
        query = select(cls.model).where(and_(*conditions))

        result = await session.execute(query)
        return result.scalars().first()



        result = await session.execute(stmt)
        # Возвращаем список кортежей: (session_id, start_time, preview)
        return [(row.session_id, row.start_time, row.message[:50]) for row in result]

    @classmethod
    async def get_by_session(cls, session, user_id: int, session_id: str):
        stmt = (
            select(cls.model)
            .where(cls.model.user_id == user_id, cls.model.session_id == session_id)
            .order_by(cls.model.timestamp)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
