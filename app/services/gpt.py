import json
from openai import OpenAI

MAX_HISTORY_MESSAGES = 4




async def process_message(user_message: str, redis_client, system_prompt: str, history_key: str, model: str,
                          client: OpenAI, temperature: float, frequency_penalty: float, presence_penalty: float):

    history_json = await redis_client.get(history_key)
    full_history = json.loads(history_json) if history_json else []
    trimmed_history = full_history[-MAX_HISTORY_MESSAGES:]

    messages = [{"role": "system", "content": system_prompt}]+trimmed_history
    messages.append({"role": "user", "content": user_message})



    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    reply = response.choices[0].message.content.strip()
    full_history.append({"role": "user", "content": user_message})
    full_history.append({"role": "assistant", "content": reply})
    await redis_client.set(history_key, json.dumps(full_history))

    return reply
