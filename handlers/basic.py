"""Файл с хендлерами бота."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start."""
    keyboard = [
        # Каждый элемент списка - это ряд кнопок
        [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_interface")],
        [InlineKeyboardButton("💬 Диалог с личностью", callback_data="talk_interface")],
        [InlineKeyboardButton("❓ Квиз", callback_data="quiz_interface")],
        [InlineKeyboardButton("🌍 Переводчик", callback_data="translate")],
        [InlineKeyboardButton("🎭 Рекомендации", callback_data="recommend_interface")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

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

    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок главного меню"""
    query = update.callback_query
    await query.answer()

    if query.data == "recommend_interface":
        from handlers.recommendations import show_categories
        await show_categories(update, context)


async def start_menu_again(query):
    """Возврат в главное меню"""
    keyboard = [
        [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_interface")],
        [InlineKeyboardButton("👥 Диалог с личностью", callback_data="talk_interface")],
        [InlineKeyboardButton("❓ Квиз", callback_data="quiz_interface")],
        [InlineKeyboardButton("🌍 Переводчик", callback_data="translate")],
        [InlineKeyboardButton("🎭 Рекомендации", callback_data="recommend_interface")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "Выберите одну из доступных функций:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )