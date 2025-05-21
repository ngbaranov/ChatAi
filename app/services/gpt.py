import json
from openai import OpenAI

MAX_HISTORY_MESSAGES = 4




async def process_message(user_message: str, redis_client, system_prompt: str, history_key: str, model: str,
                          client: OpenAI, temperature: float, frequency_penalty: float, presence_penalty: float):
    """Функция извлекает историю переписки из Redis по ключу history_key,
    Если история не найдена, инициализирует пустой список.
    Обрезаем историю, для экономии токенов и повышении производительности
    """
    history_json = await redis_client.get(history_key)
    full_history = json.loads(history_json) if history_json else []
    trimmed_history = full_history[-MAX_HISTORY_MESSAGES:]

    """
    Формирует список сообщений для отправки API, 
    Сначала идет системный промпт, затем сокращённая история, затем новое сообщение пользователя.
    """

    messages = [{"role": "system", "content": system_prompt}]+trimmed_history
    messages.append({"role": "user", "content": user_message})

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

    """
    Извлекает ответ ИИ из полученного ответа от API и очищает лишние пробелы.
    """
    reply = response.choices[0].message.content.strip()

    """
    Добавляет новое сообщение пользователя и ответ ИИ в историю.
    Сохраняет обновленную историю в Redis.
    """
    full_history.append({"role": "user", "content": user_message})
    full_history.append({"role": "assistant", "content": reply})
    await redis_client.set(history_key, json.dumps(full_history))

    """
    Возвращает ответ ИИ клиенту.
    """

    return reply
