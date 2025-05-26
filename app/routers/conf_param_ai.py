import json

from fastapi import Body, APIRouter

from app.routers.index import redis_client
from app.utils.settings import CONFIG_KEY, DEFAULT_CONFIG

router = APIRouter(prefix='/config')

@router.post("/set_config")
async def set_config(data: dict = Body(...)):
    await redis_client.set(CONFIG_KEY, json.dumps(data))
    return {"status": "ok", "message": "Настройки обновлены"}


@router.get("/get_config")
async def get_config():
    config_json = await redis_client.get(CONFIG_KEY)
    if config_json:
        return json.loads(config_json)
    return DEFAULT_CONFIG