import os

from openai import AsyncOpenAI


def get_client_for_model(model_name: str) -> AsyncOpenAI:
    """
    Выбор клиента AsyncOpenAI в зависимости от названия модели
    :param model_name:
    :return:
    """
    if model_name.startswith("deepseek"):
        return AsyncOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
    else:
        return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))