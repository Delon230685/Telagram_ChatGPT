"""Файл с хендлерами бота."""  # Документация модуля - содержит основные обработчики бота

# Импорт модуля логирования для записи событий
import logging

# Импорт необходимых классов из библиотеки python-telegram-bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Создание логгера для текущего модуля
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start."""  # Документация функции

    # Создание клавиатуры с inline-кнопками
    keyboard = [
        # Каждый элемент списка - это ряд кнопок
        [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_interface")],
        [InlineKeyboardButton("💬 Диалог с личностью", callback_data="talk_interface")],
        [InlineKeyboardButton("❓ Квиз", callback_data="quiz_interface")],
        [InlineKeyboardButton("🌍 Переводчик", callback_data="translate")],
        [InlineKeyboardButton("🎭 Рекомендации", callback_data="recommend_interface")],
    ]
    # Преобразование клавиатуры в формат Telegram
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Текст приветственного сообщения с HTML-разметкой
    welcome_text = (
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "🚀 <b>Доступные функции:</b>\n"
        "🎲 Рандомный факт - получи интересный факт\n"
        "🤖 ChatGPT - общение с ИИ\n"
        "💬 Диалог с личностью - говори с известными людьми\n"
        "❓ Квиз - проверь свои знания\n"
        "🌍 Переводчик - перевод текста на разные языки\n"
        "🎭 Рекомендации - рекомендации фильмов, книг и музыки\n\n"
        "Выберите функцию из меню ниже:"
    )

    # Отправка сообщения с клавиатурой
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',  # Разрешение HTML-разметки
        reply_markup=reply_markup  # Прикрепление клавиатуры
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок главного меню"""  # Документация функции

    # Получение callback-запроса от нажатой кнопки
    query = update.callback_query
    # Подтверждение получения callback (убирает "часики" на кнопке)
    await query.answer()

    # Проверка, какая именно кнопка была нажата
    if query.data == "recommend_interface":
        # Динамический импорт функции для избежания циклических импортов
        from handlers.recommendations import show_categories
        # Вызов функции показа категорий рекомендаций
        await show_categories(update, context)


async def start_menu_again(query):
    """Возврат в главное меню"""  # Документация функции

    # Создание аналогичной клавиатуры главного меню
    keyboard = [
        [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_interface")],
        [InlineKeyboardButton("👥 Диалог с личностью", callback_data="talk_interface")],
        [InlineKeyboardButton("❓ Квиз", callback_data="quiz_interface")],
        [InlineKeyboardButton("🌍 Переводчик", callback_data="translate")],
        [InlineKeyboardButton("🎭 Рекомендации", callback_data="recommend_interface")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Редактирование существующего сообщения для возврата в главное меню
    await query.edit_message_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "Выберите одну из доступных функций:",
        parse_mode='HTML',  # Разрешение HTML-разметки
        reply_markup=reply_markup  # Обновление клавиатуры
    )