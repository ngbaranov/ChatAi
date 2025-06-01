from typing import Annotated
from fastapi import Depends
from auth.service.token_jvt import request_token
from jose import jwt, ExpiredSignatureError, JWTError

from settings import settings
from fastapi import HTTPException, status


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


async def get_current_user(token: Annotated[str, Depends(request_token)]):
    """
    Получаем и проверяем JWT токен из запроса, расшифровываем его и извлечь из него данные о текущем пользователе
    если что то пошло не так, то возвращаем ошибку
    :param token:
    :return:
    """
    try:
        # Расшифровываем JWT токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        is_admin: str = payload.get('is_admin')
        is_superuser: str = payload.get('is_superuser')
        expire = payload.get('exp')
        # Проверяем, что все данные есть
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user'
            )
        # Если нет exp — тоже ошибка, потому что не указан срок действия токена.
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        return {
            'username': username,
            'id': user_id,
            'is_admin': is_admin,
            'is_superuser': is_superuser,
        }
    # Если истекло время действия токена
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired!"
        )
    # Если токен поврежден или невалиден
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )


async def get_current_admin_user(admin_user: Annotated[dict, Depends(get_current_user)]):
    """
    Проверяем, что пользователь является админом
    :param admin_user:
    :return:
    """
    if not admin_user['is_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not enough permissions'
        )
    return admin_user