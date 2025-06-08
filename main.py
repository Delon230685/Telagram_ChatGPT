"""Основной модуль запуска Telegram-бота"""
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from config import TG_BOT_TOKEN
from handlers import basic, random_fact, chatgpt_interface, personality_chat, quiz, translate, recommendations
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    try:
        application = Application.builder().token(TG_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", basic.start))
        application.add_handler(CommandHandler("random", random_fact.random_fact))
        application.add_handler(CommandHandler("gpt", chatgpt_interface.gpt_command))
        application.add_handler(CommandHandler("talk", personality_chat.talk_command))
        application.add_handler(CommandHandler("quiz", quiz.quiz_command))
        application.add_handler(CommandHandler("translate", translate.translate_command))
        application.add_handler(CommandHandler("recommend", recommendations.recommend_command))
        translate.setup_translate_handlers(application)
        recommendations.setup_recommend_handlers(application)

        gpt_conversation = ConversationHandler(
            entry_points=[CallbackQueryHandler(chatgpt_interface.gpt_start, pattern="^gpt_interface$")],
            states={
                chatgpt_interface.WAITING_FOR_MESSAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, chatgpt_interface.handle_gpt_message)
                ],
            },
            fallbacks=[
                CommandHandler("start", basic.start),
                CallbackQueryHandler(basic.menu_callback, pattern="^(gpt_finish|main_menu)$")
            ],
            per_message=True,
        )

        personality_conversation = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(personality_chat.talk_start, pattern="^talk_interface$"),
                CommandHandler("talk", personality_chat.talk_command)
            ],
            states={
                personality_chat.SELECTING_PERSONALITY: [
                    CallbackQueryHandler(personality_chat.personality_selected, pattern="^personality_")
                ],
                personality_chat.CHATTING_WITH_PERSONALITY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, personality_chat.handle_personality_message),
                    CallbackQueryHandler(personality_chat.handle_personality_callback,
                                         pattern="^(continue_chat|change_personality|finish_talk)$")
                ],
            },
            fallbacks=[
                CommandHandler("start", basic.start),
                CallbackQueryHandler(basic.menu_callback, pattern="^main_menu$")
            ],
        )

        quiz_conversation = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(quiz.quiz_start, pattern="^quiz_interface$"),
                CommandHandler("quiz", quiz.quiz_command)
            ],
            states={
                quiz.SELECTING_TOPIC: [
                    CallbackQueryHandler(quiz.topic_selected, pattern="^quiz_topic_")
                ],
                quiz.ANSWERING_QUESTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, quiz.handle_quiz_answer),
                    CallbackQueryHandler(quiz.handle_quiz_callback,
                                         pattern="^(quiz_continue_|quiz_change_topic|quiz_finish)$")
                ],
            },
            fallbacks=[
                CommandHandler("start", basic.start),
                CallbackQueryHandler(basic.menu_callback, pattern="^main_menu$")
            ],
        )
        application.add_handler(quiz_conversation)
        application.add_handler(personality_conversation)
        application.add_handler(gpt_conversation)
        application.add_handler(CallbackQueryHandler(random_fact.random_fact_callback, pattern="^random_"))
        application.add_handler(CallbackQueryHandler(recommendations.recommend_callback, pattern="^recommend_"))
        application.add_handler(CallbackQueryHandler(basic.menu_callback))

        logger.info("Бот запущен успешно!")

        application.run_polling()

    except Exception as e:
        logger.error(f'Ошибка при запуске: {str(e)}', exc_info=True)

if __name__ == "__main__":
    main()