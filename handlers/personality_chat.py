# Импорт модуля логирования
import logging
# Импорт необходимых компонентов из библиотеки python-telegram-bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
# Импорт функции для получения ответа от ChatGPT в роли личности
from services.openai_client import get_personality_response
# Импорт функций для работы с личностями
from data.personalities import get_personality_keyboard, get_personality_data
# Импорт модуля для работы с файловой системой
import os

# Создание логгера для текущего модуля
logger = logging.getLogger(__name__)

# Определение состояний для ConversationHandler
SELECTING_PERSONALITY, CHATTING_WITH_PERSONALITY = range(2)


async def talk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /talk - перенаправляет в talk_start"""
    await talk_start(update, context)


async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск интерфейса выбора личности"""
    try:
        # Путь к изображению для интерфейса
        image_path = "data/images/personality.jpg"
        # Текст сообщения с описанием возможностей
        message_text = (
            "👥 <b>Диалог с известной личностью</b>\n\n"
            "Выберите, с кем хотите поговорить:\n\n"
            "🧬 <b>Альберт Эйнштейн</b> - физика и философия\n"
            "🎭 <b>Уильям Шекспир</b> - поэзия и драматургия\n"
            "🎨 <b>Леонардо да Винчи</b> - искусство и изобретения\n"
            "📱 <b>Стив Джобс</b> - технологии и инновации\n"
            "📝 <b>Александр Пушкин</b> - русская поэзия\n\n"
            "Выберите личность:"
        )

        # Получаем клавиатуру с кнопками личностей
        keyboard = get_personality_keyboard()

        # Обработка callback query (если переход из другого меню)
        if update.callback_query:
            if os.path.exists(image_path):
                # Удаляем старое сообщение и отправляем новое с фото
                await update.callback_query.message.delete()
                with open(image_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=update.callback_query.message.chat_id,
                        photo=photo,
                        caption=message_text,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            else:
                # Редактируем существующее сообщение (без фото)
                await update.callback_query.edit_message_text(
                    message_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            await update.callback_query.answer()
        else:
            # Обработка обычной команды /talk
            if os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=message_text,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            else:
                await update.message.reply_text(
                    message_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )

        return SELECTING_PERSONALITY

    except Exception as e:
        logger.error(f"Ошибка при запуске диалога с личностями: {e}")
        error_text = "😔 Произошла ошибка при запуске диалога. Попробуйте позже."

        if update.callback_query:
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)

        return -1  # Завершение ConversationHandler


async def personality_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора конкретной личности"""
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback

    try:
        # Извлекаем ключ личности из callback_data
        personality_key = query.data.replace("personality_", "")
        # Получаем данные о личности
        personality = get_personality_data(personality_key)

        if not personality:
            # Обработка случая, когда личность не найдена
            if query.message.photo:
                await query.edit_message_caption("❌ Ошибка: личность не найдена.")
            else:
                await query.edit_message_text("❌ Ошибка: личность не найдена.")
            return -1

        # Сохраняем выбранную личность в user_data
        context.user_data['current_personality'] = personality_key
        context.user_data['personality_data'] = personality

        # Формируем текст сообщения
        message_text = (
            f"{personality['emoji']} <b>Диалог с {personality['name']}</b>\n\n"
            f"Теперь вы можете общаться с {personality['name']}!\n\n"
            "💬 Просто напишите ваше сообщение, и личность ответит в своем стиле.\n\n"
            "✍️ Напишите что-нибудь:"
        )

        # Проверяем, есть ли в сообщении фото
        if query.message.photo:
            # Редактируем подпись к фото
            await query.edit_message_caption(
                caption=message_text,
                parse_mode='HTML'
            )
        else:
            # Редактируем текстовое сообщение
            await query.edit_message_text(
                text=message_text,
                parse_mode='HTML'
            )

        return CHATTING_WITH_PERSONALITY  # Переход в состояние диалога

    except Exception as e:
        logger.error(f"Ошибка при выборе личности: {e}")
        try:
            # Пытаемся отправить сообщение об ошибке
            if query.message.photo:
                await query.edit_message_caption("😔 Произошла ошибка. Попробуйте еще раз.")
            else:
                await query.edit_message_text("😔 Произошла ошибка. Попробуйте еще раз.")
        except Exception:
            # Fallback: отправляем новое сообщение
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="😔 Произошла ошибка. Попробуйте еще раз."
            )
        return -1


async def handle_personality_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщения для выбранной личности"""
    try:
        user_message = update.message.text
        # Получаем данные о выбранной личности
        personality_key = context.user_data.get('current_personality')
        personality_data = context.user_data.get('personality_data')

        if not personality_key or not personality_data:
            await update.message.reply_text(
                "❌ Произошла ошибка: личность не выбрана. Используйте /talk для начала."
            )
            return -1

        # Показываем индикатор "печатает"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        # Отправляем сообщение о обработке
        processing_msg = await update.message.reply_text(
            f"{personality_data['emoji']} {personality_data['name']} размышляет... ⏳"
        )

        # Получаем ответ от ChatGPT в стиле выбранной личности
        personality_response = await get_personality_response(user_message, personality_data['prompt'])

        # Создаем клавиатуру с кнопками управления
        keyboard = [
            [InlineKeyboardButton("💬 Продолжить диалог", callback_data="continue_chat")],
            [InlineKeyboardButton("👥 Выбрать другую личность", callback_data="change_personality")],
            [InlineKeyboardButton("🏠 Закончить", callback_data="finish_talk")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Удаляем сообщение о обработке и отправляем ответ
        await processing_msg.delete()
        await update.message.reply_text(
            f"{personality_data['emoji']} <b>{personality_data['name']} отвечает:</b>\n\n{personality_response}",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        return CHATTING_WITH_PERSONALITY  # Остаемся в состоянии диалога

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения для личности: {e}")
        await update.message.reply_text(
            "😔 Произошла ошибка при обработке сообщения. Попробуйте еще раз."
        )
        return CHATTING_WITH_PERSONALITY


async def handle_personality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback-кнопок в диалоге с личностью"""
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback

    if query.data == "continue_chat":
        # Продолжение диалога с текущей личностью
        personality_data = context.user_data.get('personality_data')
        if personality_data:
            await query.edit_message_text(
                f"{personality_data['emoji']} <b>Продолжаем диалог с {personality_data['name']}</b>\n\n"
                "💬 Напишите ваше следующее сообщение:",
                parse_mode='HTML'
            )
            return CHATTING_WITH_PERSONALITY

    elif query.data == "change_personality":
        # Возврат к выбору личности
        return await talk_start(update, context)

    elif query.data == "finish_talk":
        # Завершение диалога - очищаем данные
        context.user_data.pop('current_personality', None)
        context.user_data.pop('personality_data', None)
        return -1  # Завершение ConversationHandler

    return CHATTING_WITH_PERSONALITY