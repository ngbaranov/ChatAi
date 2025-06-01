from datetime import datetime, timedelta, timezone
from jose import jwt
from settings import settings
from fastapi import HTTPException, Request

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


async def create_access_token(username: str, user_id: int, is_admin: bool, expires_delta: timedelta):
    """
    Генерируем JWT токен
    :param username:
    :param user_id:
    :param is_admin:
    :param expires_delta:
    :return:
    """
    encode = {'sub': username, 'id': user_id, 'is_admin': is_admin}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def request_token(request: Request):
    """
    Получаем JWT токен из куки и возвращаем
    :param request:
    :return:
    """
    token = request.cookies.get('access_token')
    if token is None:
        raise HTTPException(status_code=401, detail="No access token supplied")
    return token