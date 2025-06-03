import json

from fastapi import Body, APIRouter, Request

from app.routers.index import redis_client
from app.services.get_token import get_user_id
from app.utils.variables import CONFIG_KEY, DEFAULT_CONFIG

router = APIRouter(prefix='/config')

@router.post("/set_config")
async def set_config(request: Request, data: dict = Body(...)):
    """
    Сохраняет конфигурацию ИИ в Redis под ключом пользователя
    """
    user_id = get_user_id(request)
    user_config_key = f"chat:{user_id}:config"
    await redis_client.set(user_config_key, json.dumps(data))
    return {"status": "ok", "message": "Настройки обновлены"}



@router.get("/get_config")
async def get_config(request: Request):
    """
    Возвращает конфигурацию ИИ пользователя
    """
    user_id = get_user_id(request)
    user_config_key = f"chat:{user_id}:config"
    config_json = await redis_client.get(user_config_key)
    if config_json:
        return json.loads(config_json)
    return DEFAULT_CONFIG
