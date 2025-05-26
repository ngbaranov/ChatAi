from fastapi import FastAPI

from app.routers import index, conf_param_ai


app = FastAPI()


app.include_router(index.router)
app.include_router(conf_param_ai.router)
