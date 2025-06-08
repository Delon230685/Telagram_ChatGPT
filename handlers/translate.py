"""Файл обработки команд для перевода текста"""
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from services.openai_client import get_chatgpt_response

logger = logging.getLogger(__name__)

SELECT_LANG, WAIT_TEXT = range(2)

LANGUAGES = {
    "en": "🇬🇧 Английский",
    "es": "🇪🇸 Испанский",
    "fr": "🇫🇷 Французский", 
    "de": "🇩🇪 Немецкий",
    "ja": "🇯🇵 Японский",
    "zh": "🇨🇳 Китайский"
}


async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /translate - перенаправляет в show_lang_menu"""
    return await show_lang_menu(update, context)


async def show_lang_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображение меню выбора языка перевода"""
    try:
        keyboard = [
            [InlineKeyboardButton(lang, callback_data=f"lang_{code}")]
            for code, lang in LANGUAGES.items()
        ]
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        image_path = os.path.join('data', 'images', 'translate.jpg')
        caption = "🌍 <b>Переводчик текста</b>\n\nВыберите язык для перевода:"

        if update.callback_query:
            await update.callback_query.answer()
            if os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=caption,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=caption,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
        else:
            if os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=caption,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
            else:
                await update.message.reply_text(
                    caption,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )

        return SELECT_LANG

    except Exception as e:
        logger.error(f"Ошибка в show_lang_menu: {e}")
        await send_error(update, "Ошибка при запуске переводчика")
        return ConversationHandler.END


async def lang_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора языка пользователем"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Перевод отменён"
        )
        return ConversationHandler.END

    lang_code = query.data.split("_")[1]
    context.user_data["target_lang"] = lang_code
    lang_name = LANGUAGES[lang_code]

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"🌍 Выбран язык: <b>{lang_name}</b>\n\nВведите текст для перевода:",
        parse_mode='HTML'
    )

    return WAIT_TEXT


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текста для перевода"""
    try:
        text = update.message.text
        lang_code = context.user_data.get("target_lang")
        lang_name = LANGUAGES.get(lang_code, "")

        if not lang_code:
            await update.message.reply_text("❌ Язык не выбран. Используйте /translate")
            return ConversationHandler.END

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        processing_msg = await update.message.reply_text("🔄 Перевод... ⏳")

        try:
            prompt = f"Переведи следующий текст на {lang_name}. Сохрани форматирование и смысл:\n\n{text}"
            translated = await get_chatgpt_response(prompt, mode="translate")
        except Exception as e:
            logger.error(f"Ошибка при запросе к ChatGPT: {e}")
            translated = "⚠️ Произошла ошибка при переводе. Пожалуйста, попробуйте позже."

        keyboard = [
            [InlineKeyboardButton("🔄 Новый текст", callback_data="new_text")],
            [InlineKeyboardButton("🌍 Сменить язык", callback_data="change_lang")],
            [InlineKeyboardButton("🏠 В меню", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await processing_msg.delete()
        await update.message.reply_text(
            f"🌍 <b>Перевод на {lang_name}:</b>\n\n{translated}",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        return WAIT_TEXT

    except Exception as e:
        logger.error(f"Ошибка в handle_text: {e}")
        await send_error(update, "Ошибка при обработке перевода")
        return WAIT_TEXT


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback-кнопок после перевода"""
    query = update.callback_query
    await query.answer()

    if query.data == "new_text":
        lang_code = context.user_data.get("target_lang")
        lang_name = LANGUAGES.get(lang_code, "")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"Введите текст для перевода на <b>{lang_name}</b>:",
            parse_mode='HTML'
        )
        return WAIT_TEXT

    elif query.data == "change_lang":
        return await show_lang_menu(update, context)

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="✅ Перевод завершён"
    )
    return ConversationHandler.END

async def send_error(update: Update, text: str):
    """Унифицированная функция отправки сообщений об ошибках"""
    error_msg = f"⚠️ {text}"
    if update.callback_query:
        await update.callback_query.message.reply_text(error_msg)
    else:
        await update.message.reply_text(error_msg)

def setup_translate_handlers(app):
    """Настройка обработчиков для системы перевода"""
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('translate', translate_command),
            CallbackQueryHandler(translate_command, pattern="^translate$")
        ],
        states={
            SELECT_LANG: [CallbackQueryHandler(lang_selected, pattern=r"^lang_\w+|cancel$")],
            WAIT_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(handle_callback, pattern=r"^new_text|change_lang|cancel$")
            ],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)],
    )
    app.add_handler(conv_handler)