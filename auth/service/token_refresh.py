from datetime import datetime, timezone, timedelta
from settings import settings

from jose import jwt

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


async def create_refresh_token(user_id: int, expires_delta: timedelta):
    """
    Генерируем refresh token (только user_id, без username и is_admin)
    """
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)