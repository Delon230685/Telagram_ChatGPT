"""Файл обработки команд для рекомендаций фильмов, музыки, игр и книг"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, ConversationHandler
from services.openai_client import get_chatgpt_response

logger = logging.getLogger(__name__)

SELECT_CATEGORY, SELECT_GENRE = range(2)

CATEGORIES = {
    "movies": "🎬 Фильмы",
    "books": "📚 Книги",
    "music": "🎵 Музыка",
    "games": "🎮 Игры"
}

GENRES = {
    "movies": ["🔫 Боевик", "😂 Комедия", "🎭 Драма", "🚀 Фантастика", "💘 Мелодрама"],
    "books": ["🧙 Фэнтези", "🕵️ Детектив", "🚀 Научная фантастика", "💔 Роман", "📖 Классика"],
    "music": ["🎤 Поп", "🎸 Рок", "🎷 Джаз", "🎹 Электроника", "🎶 Хип-хоп"],
    "games": ["🎮 Экшен", "🧩 Головоломки", "🌍 Открытый мир", "👾 RPG", "🏎️ Гонки"]
}

RECOMMENDATION_TEMPLATES = {
    "movies": "Дай 3 рекомендации фильмов в жанре {genre}. Укажи год выпуска и краткое описание.",
    "books": "Предложи 3 книги в жанре {genre}. Укажи автора, год издания и краткое описание.",
    "music": "Порекомендуй 3 музыкальных альбома или исполнителей в жанре {genre}. Укажи год выпуска.",
    "games": "Назови 3 игры в жанре {genre}. Укажи платформы, год выхода и краткое описание."
}


async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /recommend - перенаправляет в show_categories"""
    return await show_categories(update, context)

async def recommend_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для кнопки рекомендаций"""
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback
    return await show_categories(update, context)

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображение списка категорий рекомендаций"""
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"cat_{code}")]
        for code, name in CATEGORIES.items()
    ]
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎭 <b>Выберите категорию рекомендаций:</b>",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🎭 <b>Выберите категорию рекомендаций:</b>",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    return SELECT_CATEGORY


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории пользователем"""
    query = update.callback_query
    await query.answer()

    # Обработка отмены
    if query.data == "cancel":
        await query.edit_message_text("❌ Рекомендации отменены")
        return ConversationHandler.END

    category = query.data.split("_")[1]
    context.user_data["category"] = category

    genres = GENRES[category]
    keyboard = []

    for i in range(0, len(genres), 2):
        if i + 1 < len(genres):
            keyboard.append([
                InlineKeyboardButton(genres[i], callback_data=f"genre_{i}"),
                InlineKeyboardButton(genres[i + 1], callback_data=f"genre_{i + 1}")
            ])
        else:
            keyboard.append([InlineKeyboardButton(genres[i], callback_data=f"genre_{i}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])

    await query.edit_message_text(
        f"🎭 <b>Выберите жанр для {CATEGORIES[category]}:</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return SELECT_GENRE


async def select_genre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора жанра и получение рекомендаций"""
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        return await show_categories(update, context)

    genre_idx = int(query.data.split("_")[1])
    category = context.user_data["category"]
    selected_genre = GENRES[category][genre_idx]

    context.user_data["genre"] = selected_genre
    context.user_data["genre_idx"] = genre_idx

    await query.edit_message_text("🔄 <b>Ищу рекомендации...</b>", parse_mode='HTML')

    try:
        prompt = RECOMMENDATION_TEMPLATES[category].format(genre=selected_genre)
        recommendations = await get_chatgpt_response(prompt)

        if not recommendations:
            raise ValueError("Пустой ответ от API")

        keyboard = [
            [InlineKeyboardButton("🔄 Новые рекомендации", callback_data=f"genre_{genre_idx}")],
            [InlineKeyboardButton("🔙 Выбрать другой жанр", callback_data=f"cat_{category}")],
            [InlineKeyboardButton("🎭 Другие категории", callback_data="back")]
        ]

        await query.edit_message_text(
            f"🎭 <b>Рекомендации {selected_genre}:</b>\n\n{recommendations}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Ошибка при получении рекомендаций: {e}")
        await query.edit_message_text(
            "⚠️ <b>Произошла ошибка при получении рекомендаций. Попробуйте позже.</b>",
            parse_mode='HTML'
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отмены рекомендаций"""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Рекомендации отменены")
    else:
        await update.message.reply_text("❌ Рекомендации отменены")
    return ConversationHandler.END  # Завершаем диалог


def setup_recommend_handlers(app):
    """Настройка обработчиков для системы рекомендаций"""
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('recommend', recommend_command),
            CommandHandler('recommendations', recommend_command),
            CallbackQueryHandler(recommend_callback, pattern="^recommend_")
        ],
        states={
            SELECT_CATEGORY: [CallbackQueryHandler(select_category, pattern="^cat_|cancel$")],
            SELECT_GENRE: [CallbackQueryHandler(select_genre, pattern="^genre_|back$")]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True  # Разрешаем повторный вход в диалог
    )
    app.add_handler(conv_handler)