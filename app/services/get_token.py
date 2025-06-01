from jose import jwt, JWTError
from settings import settings
from fastapi import WebSocket


def get_user_id_from_cookie(websocket: WebSocket) -> int:
    """
    Получаем токен из куки и выделяем из него user_id
    :param websocket:
    :return:
    """
    token = websocket.cookies.get("access_token")
    if not token:
        raise RuntimeError("Нет access_token")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return int(payload.get("id"))
    except JWTError:
        raise RuntimeError("Невалидный токен")