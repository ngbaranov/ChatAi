from fastapi import FastAPI

from app.routers import index, conf_param_ai, history
from auth import auth_routher


app = FastAPI()


app.include_router(index.router)
app.include_router(conf_param_ai.router)
app.include_router(auth_routher.router)
app.include_router(history.router)
