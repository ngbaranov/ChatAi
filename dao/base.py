from sqlalchemy import select, and_
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
