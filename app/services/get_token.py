from jose import jwt, JWTError
from settings import settings
from fastapi import WebSocket, Request


def extract_token_from_scope(scope) -> str:
    if isinstance(scope, Request) or isinstance(scope, WebSocket):
        token = scope.cookies.get("access_token")
        if not token:
            raise RuntimeError("Нет access_token")
        return token
    raise RuntimeError("Неподдерживаемый тип запроса")


def get_user_id(scope: Request | WebSocket) -> int:
    token = extract_token_from_scope(scope)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return int(payload.get("id"))
    except JWTError:
        raise RuntimeError("Невалидный токен")