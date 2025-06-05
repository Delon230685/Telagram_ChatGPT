# Импорт необходимых классов из библиотеки python-telegram-bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Словарь с доступными темами для квиза
QUIZ_TOPICS = {
    # Тема "Программирование"
    "programming": {
        "name": "💻 Программирование",  # Название темы с иконкой
        "emoji": "💻",  # Эмодзи для темы
        "prompt": """Ты создаешь вопросы для квиза по программированию. 
Создай один интересный вопрос средней сложности с 4 вариантами ответа (A, B, C, D). 
Укажи правильный ответ в конце. 
Формат:
Вопрос: [твой вопрос]
A) [вариант 1]
B) [вариант 2] 
C) [вариант 3]
D) [вариант 4]
Правильный ответ: [буква]"""  # Шаблон для генерации вопросов
    },

    # Тема "История"
    "history": {
        "name": "🏛️ История",
        "emoji": "🏛️",
        "prompt": """Ты создаешь вопросы для квиза по истории..."""  # Аналогичный шаблон для истории
    },

    # Тема "Наука"
    "science": {
        "name": "🔬 Наука",
        "emoji": "🔬",
        "prompt": """Ты создаешь вопросы для квиза по науке..."""
    },

    # Тема "География"
    "geography": {
        "name": "🌍 География",
        "emoji": "🌍",
        "prompt": """Ты создаешь вопросы для квиза по географии..."""
    },

    # Тема "Кино"
    "movies": {
        "name": "🎬 Кино",
        "emoji": "🎬",
        "prompt": """Ты создаешь вопросы для квиза о кино..."""
    }
}


# Функция создания клавиатуры с темами квиза
def get_quiz_topics_keyboard():
    """Возвращает клавиатуру с темами квиза"""
    keyboard = []  # Инициализация пустого списка для кнопок

    # Создание кнопок для каждой темы
    for topic_key, topic_data in QUIZ_TOPICS.items():
        # Добавление кнопки с названием темы
        keyboard.append([InlineKeyboardButton(topic_data["name"], callback_data=f"quiz_topic_{topic_key}")])

    # Добавление кнопки возврата в главное меню
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])

    # Возврат готовой клавиатуры
    return InlineKeyboardMarkup(keyboard)


# Функция получения данных темы по её ключу
def get_quiz_topic_data(topic_key):
    """Возвращает данные темы по ключу"""
    return QUIZ_TOPICS.get(topic_key)  # Возвращает None если тема не найдена


# Функция создания клавиатуры для продолжения квиза
def get_quiz_continue_keyboard(topic_key):
    """Возвращает клавиатуру для продолжения квиза"""
    keyboard = [
        # Кнопка для получения следующего вопроса
        [InlineKeyboardButton("🎯 Ещё вопрос", callback_data=f"quiz_continue_{topic_key}")],

        # Кнопка для смены темы
        [InlineKeyboardButton("🔄 Сменить тему", callback_data="quiz_change_topic")],

        # Кнопка завершения квиза
        [InlineKeyboardButton("🏁 Закончить квиз", callback_data="quiz_finish")]
    ]
    return InlineKeyboardMarkup(keyboard)  # Возврат готовой клавиатуры