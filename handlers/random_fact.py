# Импорт модуля логирования
import logging
# Импорт необходимых компонентов из библиотеки python-telegram-bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
# Импорт функции для получения случайных фактов
from services.openai_client import get_random_fact

# Создание логгера для текущего модуля
logger = logging.getLogger(__name__)


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основная функция для обработки команды /random_fact"""
    try:
        # Отправляем сообщение о загрузке факта
        loading_msg = await update.message.reply_text("🎲 Генерирую интересный факт... ⏳")
        # Получаем случайный факт через API
        fact = await get_random_fact()

        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
            [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Заменяем сообщение о загрузке на полученный факт
        await loading_msg.edit_text(
            f"🧠 <b>Интересный факт:</b>\n\n{fact}",
            parse_mode='HTML',  # Разрешаем HTML-разметку
            reply_markup=reply_markup  # Добавляем кнопки
        )

    except Exception as e:
        # Логируем ошибку и уведомляем пользователя
        logger.error(f"Ошибка при получении факта: {e}")
        await update.message.reply_text(
            "🤔 К сожалению, не удалось получить факт в данный момент. Попробуйте позже!"
        )


async def random_fact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback-кнопок для работы с фактами"""
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback

    # Обработка кнопки "Хочу ещё факт"
    if query.data == "random_more":
        try:
            # Обновляем сообщение - показываем загрузку
            await query.edit_message_text("🎲 Генерирую новый факт... ⏳")
            # Получаем новый факт
            fact = await get_random_fact()

            # Создаем те же кнопки
            keyboard = [
                [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
                [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Обновляем сообщение с новым фактом
            await query.edit_message_text(
                f"🧠 <b>Интересный факт:</b>\n\n{fact}",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Ошибка при получении нового факта: {e}")
            await query.edit_message_text(
                "😔 Произошла ошибка. Попробуйте позже.\n"
                "Используйте /start чтобы вернуться в меню."
            )

    # Обработка кнопки "Закончить"
    elif query.data == "random_finish":
        # Создаем клавиатуру главного меню
        keyboard = [
            [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
            [InlineKeyboardButton("🤖 ChatGPT (скоро)", callback_data="gpt_coming_soon")],
            [InlineKeyboardButton("👥 Диалог с личностью (скоро)", callback_data="talk_coming_soon")],
            [InlineKeyboardButton("🧠 Квиз (скоро)", callback_data="quiz_coming_soon")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Возвращаем пользователя в главное меню
        await query.edit_message_text(
            "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
            "Выберите одну из доступных функций:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    # Обработка кнопки "Рандомный факт" из меню
    elif query.data == "random_fact":
        try:
            # Показываем сообщение о загрузке
            await query.edit_message_text("🎲 Генерирую интересный факт... ⏳")
            # Получаем новый факт
            fact = await get_random_fact()

            # Создаем кнопки управления
            keyboard = [
                [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
                [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Показываем полученный факт
            await query.edit_message_text(
                f"🧠 <b>Интересный факт:</b>\n\n{fact}",
                parse_mode='HTML',
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Ошибка при получении факта из меню: {e}")
            await query.edit_message_text(
                "😔 Произошла ошибка. Попробуйте позже.\n"
                "Используйте /start чтобы вернуться в меню."
            )