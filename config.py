# Импорт модуля os для работы с переменными окружения
import os

# Импорт функции load_dotenv из библиотеки python-dotenv
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env в текущем каталоге
load_dotenv()

# Получение токена Telegram-бота из переменных окружения
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")

# Получение токена ChatGPT из переменных окружения
CHATGPT_TOKEN = os.getenv("CHATGPT_TOKEN")

# Проверка, что оба токена установлены
if not all([TG_BOT_TOKEN, CHATGPT_TOKEN]):
    # Если какой-то токен отсутствует - вызываем исключение с сообщением
    raise ValueError("Введите токены в .env")
