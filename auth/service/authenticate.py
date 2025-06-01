from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from dao.dao import UserDAO
from database.db_depends import get_db
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def authenticate_user(db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str):
    """
    выполняет аутентификацию пользователя, т.е. проверяет логин и пароль
    :param db:
    :param username:
    :param password:
    :return: user
    """

    # Проверяем, что пользователь с таким именем уже существует
    user = await UserDAO.get_by_field(db, username=username)
    # Если пользователь не найден или пароли не совпадают, то возвращаем ошибку, иначе возвращаем пользователя
    if not user or not bcrypt_context.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user