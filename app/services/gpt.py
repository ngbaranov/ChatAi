import json
from openai import AsyncOpenAI

MAX_HISTORY_MESSAGES = 4
MAX_STORED_MESSAGES = 50




async def process_message(user_id: int, user_message: str, redis_client, system_prompt: str, history_key: str, model: str,
                          client: AsyncOpenAI, temperature: float, frequency_penalty: float, presence_penalty: float):
    """
    Обрабатывает новое сообщение пользователя и взаимодействует с OpenAI API,
    сохраняя историю в Redis как список элементов.
    """

    history_key = f"chat:{user_id}:history"
    # 1) Читаем всю историю списка из Redis
    raw_history = await redis_client.lrange(history_key, 0, -1)
    full_history = [json.loads(item) for item in raw_history]

    # дополнительно меняем роль "bot" на "assistant"
    for msg in full_history:
        if msg.get("role") == "bot":
            msg["role"] = "assistant"

    # 2) Обрезаем историю для контекста модели
    trimmed_history = full_history[-MAX_HISTORY_MESSAGES:]

    # 3) Формируем payload для API: системный промпт, сокращённая история, новое сообщение
    messages = [
        {"role": "system", "content": system_prompt}
    ] + trimmed_history + [
        {"role": "user", "content": user_message}
    ]

    """
    Отправляет запрос в OpenAI API для получения ответа.
    """

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    # Извлекает ответ ИИ из полученного ответа от API и очищает лишние пробелы.

    reply = response.choices[0].message.content.strip()

    # 5) Сохраняем новые сообщения в Redis (список)
    await redis_client.rpush(history_key, json.dumps({"role": "user", "content": user_message}))
    await redis_client.rpush(history_key, json.dumps({"role": "assistant", "content": reply}))
    # 6) Обрезаем список до последних MAX_STORED_MESSAGES элементов
    await redis_client.ltrim(history_key, -MAX_STORED_MESSAGES, -1)

    # 7) Возвращаем ответ ИИ
    return reply

