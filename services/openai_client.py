from openai import OpenAI
import logging
from config import CHATGPT_TOKEN

logger = logging.getLogger(__name__)

client = OpenAI(api_key=CHATGPT_TOKEN)


async def get_chatgpt_response(prompt: str, mode: str = "default") -> str:
    """Универсальная функция для запросов к ChatGPT"""
    try:
        system_messages = {
            "default": "Ты полезный ассистент. Отвечай на вопросы развернуто и точно. " 
              "Переводи текст ТОЛЬКО если явно указано это в запросе.",
            "translate": "Ты профессиональный переводчик.",
            "fact": "Ты энциклопедия интересных фактов.",
            "personality": "Ты исполняешь роль конкретной личности."
        }

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_messages.get(mode, "Ты полезный ассистент.")},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7 if mode == "default" else 0.3
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Ошибка ChatGPT: {e}")
        return f"Извините, произошла ошибка. {str(e)}"


async def get_random_fact() -> str:
    """Генерация случайного факта"""
    return await get_chatgpt_response("Расскажи интересный научный факт (1-2 предложения)", "fact")


async def get_personality_response(user_message: str, personality_prompt: str) -> str:
    """Генерация ответа от имени личности"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": personality_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Ошибка личности: {e}")
        return "Не удалось получить ответ. Попробуйте позже."