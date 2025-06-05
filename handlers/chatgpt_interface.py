# Импорт модуля логирования
import logging

from openai.types.beta.threads import Message
# Импорт необходимых компонентов из библиотеки python-telegram-bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
# Импорт функции для работы с ChatGPT
from services.openai_client import get_chatgpt_response
# Импорт модулей для работы с файлами
import os
from io import BytesIO

# Создание логгера для текущего модуля
logger = logging.getLogger(__name__)

# Константа состояния для ConversationHandler
WAITING_FOR_MESSAGE = 1

# Шаблон сообщения с описанием возможностей ChatGPT
CAPTION = '''🤖 <b>ChatGPT Интерфейс</b>\n\n
Напишите любой вопрос или сообщение, и я передам его ChatGPT!\n\n
💡 <b>Примеры вопросов:</b>\n
• Объясни квантовую физику простыми словами\n
• Напиши короткий рассказ про кота\n
• Как приготовить пасту карбонару?\n
• Переведи фразу на английский\n\n
✍️ Просто напишите ваш вопрос следующим сообщением:'''


async def gpt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /gpt - перенаправляет в gpt_start"""
    return await gpt_start(update, context)


async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основная функция запуска интерфейса ChatGPT"""
    try:
        # Путь к изображению для интерфейса
        image_path = os.path.join('data', 'images', 'chatgpt.jpg')

        if os.path.exists(image_path):
            try:
                # Открытие и чтение изображения
                with open(image_path, 'rb') as photo_file:
                    photo = InputFile(BytesIO(photo_file.read()), filename='chatgpt.jpg')

                # Определение цели (сообщение или callback)
                target = update.callback_query.message if update.callback_query else update.message
                # Отправка изображения с подписью
                await target.reply_photo(
                    photo=photo,
                    caption=CAPTION,
                    parse_mode='HTML'
                )
            except Exception as img_error:
                # Логирование ошибки с изображением
                logger.error(f"Ошибка изображения: {img_error}", exc_info=True)
                # Отправка текстового сообщения вместо изображения
                await send_text_message(update, CAPTION)
        else:
            # Если изображение не найдено - отправляем текст
            await send_text_message(update, CAPTION)

        # Ответ на callback_query (убирает "часики")
        if update.callback_query:
            await update.callback_query.answer()

        # Возврат состояния ожидания сообщения
        return WAITING_FOR_MESSAGE

    except Exception as e:
        # Логирование ошибки запуска
        logger.error(f"Ошибка запуска: {e}", exc_info=True)
        # Отправка сообщения об ошибке
        await send_error_message(update, "😔 Ошибка при запуске ChatGPT. Попробуйте позже.")
        return -1  # Завершение ConversationHandler


async def handle_gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка пользовательских сообщений для ChatGPT"""
    try:
        user_message = update.message.text

        # Определение типа запроса (перевод или обычный)
        if any(word in user_message.lower() for word in ["переведи", "перевод", "на английском"]):
            mode = "translate"
            prompt = f"Переведи точно: {user_message}"
        else:
            mode = "default"
            prompt = f"Ответь на вопрос:\n{user_message}\n\nОтвечай как эксперт, не предлагай другие функции."

        # Показываем индикатор "печатает"
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        # Отправляем сообщение о обработке
        processing_msg = await update.message.reply_text("🤔 Обрабатываю запрос... ⏳")
        # Получаем ответ от ChatGPT
        gpt_response = await get_chatgpt_response(prompt, mode=mode)

        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("💬 Новый вопрос", callback_data="gpt_new")],
            [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
        ]

        # Удаляем сообщение о обработке
        await processing_msg.delete()
        # Отправляем ответ с кнопками
        await update.message.reply_text(
            f"🤖 <b>Ответ:</b>\n\n{gpt_response}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard))

        # Продолжаем ожидать сообщения
        return WAITING_FOR_MESSAGE

    except Exception as e:
        # Логирование ошибки
        logger.error(f"Ошибка обработки: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ Ошибка обработки. Попробуйте снова или вернитесь в меню (/start)."
        )
        return WAITING_FOR_MESSAGE


async def gpt_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок ChatGPT"""
    query = update.callback_query
    await query.answer()

    if query.data == "gpt_new":
        if query.message and isinstance(query.message, Message):
            await query.message.edit_text(CAPTION, parse_mode='HTML')
        else:
            await query.from_user.send_message(CAPTION, parse_mode='HTML')
        return WAITING_FOR_MESSAGE
    elif query.data == "main_menu":
        from handlers.basic import start
        return await start(update, context)


async def send_text_message(update: Update, text: str):
    """Универсальная функция отправки/редактирования текстового сообщения"""
    if update.callback_query:
        # Проверяем, что message доступен и является Message
        if update.callback_query.message and isinstance(update.callback_query.message, Message):
            await update.callback_query.message.edit_text(text, parse_mode='HTML')
        else:
            # Если сообщение недоступно, отправляем новое
            await update.callback_query.answer()
            await update.callback_query.from_user.send_message(text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')


async def send_error_message(update: Update, error_text: str):
    """Функция для отправки сообщений об ошибках"""
    await send_text_message(update, error_text)


def setup_gpt_handlers(application):
    """Регистрация всех обработчиков для ChatGPT функционала"""
    # Обработчик команды /gpt
    application.add_handler(CommandHandler("gpt", gpt_command))
    # Обработчик текстовых сообщений (исключая команды и специальные слова)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex(r'^(/|start|help|quiz)'),
        handle_gpt_message))
    # Обработчик callback-кнопок, начинающихся с "gpt_"
    application.add_handler(CallbackQueryHandler(gpt_callback_handler, pattern="^gpt_"))