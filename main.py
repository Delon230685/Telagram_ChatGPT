# Импорт модуля логирования для записи событий
import logging

# Импорт необходимых компонентов из библиотеки python-telegram-bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# Импорт токена бота из файла config.py
from config import TG_BOT_TOKEN

# Импорт обработчиков команд из разных модулей
from handlers import basic, random_fact, chatgpt_interface, personality_chat, quiz, translate, recommendations

# Импорт функций для фильтрации предупреждений
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

# Игнорирование специфических предупреждений PTB (Python Telegram Bot)
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Настройка формата логов: время - имя логгера - уровень - сообщение
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Создание логгера для текущего модуля
logger = logging.getLogger(__name__)


def main():
    try:
        # Создание экземпляра бота с использованием токена
        application = Application.builder().token(TG_BOT_TOKEN).build()

        # Регистрация обработчиков команд:

        # Обработчик команды /start (базовое меню)
        application.add_handler(CommandHandler("start", basic.start))

        # Обработчик команды /random (случайный факт)
        application.add_handler(CommandHandler("random", random_fact.random_fact))

        # Обработчик команды /gpt (чат с GPT)
        application.add_handler(CommandHandler("gpt", chatgpt_interface.gpt_command))

        # Обработчик команды /talk (чат с личностью)
        application.add_handler(CommandHandler("talk", personality_chat.talk_command))

        # Обработчик команды /quiz (викторина)
        application.add_handler(CommandHandler("quiz", quiz.quiz_command))

        # Обработчик команды /translate (перевод)
        application.add_handler(CommandHandler("translate", translate.translate_command))

        # Обработчик команды /recommend (рекомендации)
        application.add_handler(CommandHandler("recommend", recommendations.recommend_command))

        # Настройка дополнительных обработчиков:

        # Обработчики для системы перевода
        translate.setup_translate_handlers(application)

        # Обработчики для системы рекомендаций
        recommendations.setup_recommend_handlers(application)

        # Настройка ConversationHandler для GPT-чата:
        gpt_conversation = ConversationHandler(
            # Точка входа - нажатие кнопки с паттерном "gpt_interface"
            entry_points=[CallbackQueryHandler(chatgpt_interface.gpt_start, pattern="^gpt_interface$")],
            # Состояния диалога:
            states={
                # В состоянии ожидания сообщения обрабатываем только текст
                chatgpt_interface.WAITING_FOR_MESSAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, chatgpt_interface.handle_gpt_message)
                ],
            },
            # Возможности выхода из диалога:
            fallbacks=[
                # Команда /start
                CommandHandler("start", basic.start),
                # Нажатие кнопок "gpt_finish" или "main_menu"
                CallbackQueryHandler(basic.menu_callback, pattern="^(gpt_finish|main_menu)$")
            ],
            # Обработка каждого сообщения отдельно
            per_message=True,
        )

        # Настройка ConversationHandler для чата с личностью:
        personality_conversation = ConversationHandler(
            # Точки входа:
            entry_points=[
                # Нажатие кнопки "talk_interface"
                CallbackQueryHandler(personality_chat.talk_start, pattern="^talk_interface$"),
                # Команда /talk
                CommandHandler("talk", personality_chat.talk_command)
            ],
            # Состояния диалога:
            states={
                # Состояние выбора личности
                personality_chat.SELECTING_PERSONALITY: [
                    # Обработка выбора личности (кнопки с паттерном "personality_")
                    CallbackQueryHandler(personality_chat.personality_selected, pattern="^personality_")
                ],
                # Состояние общения с выбранной личностью
                personality_chat.CHATTING_WITH_PERSONALITY: [
                    # Обработка текстовых сообщений
                    MessageHandler(filters.TEXT & ~filters.COMMAND, personality_chat.handle_personality_message),
                    # Обработка кнопок управления чатом
                    CallbackQueryHandler(personality_chat.handle_personality_callback,
                                         pattern="^(continue_chat|change_personality|finish_talk)$")
                ],
            },
            # Возможности выхода из диалога:
            fallbacks=[
                # Команда /start
                CommandHandler("start", basic.start),
                # Нажатие кнопки "main_menu"
                CallbackQueryHandler(basic.menu_callback, pattern="^main_menu$")
            ],
        )

        # Настройка ConversationHandler для викторины:
        quiz_conversation = ConversationHandler(
            # Точки входа:
            entry_points=[
                # Нажатие кнопки "quiz_interface"
                CallbackQueryHandler(quiz.quiz_start, pattern="^quiz_interface$"),
                # Команда /quiz
                CommandHandler("quiz", quiz.quiz_command)
            ],
            # Состояния диалога:
            states={
                # Состояние выбора темы викторины
                quiz.SELECTING_TOPIC: [
                    # Обработка выбора темы (кнопки с паттерном "quiz_topic_")
                    CallbackQueryHandler(quiz.topic_selected, pattern="^quiz_topic_")
                ],
                # Состояние ответа на вопрос
                quiz.ANSWERING_QUESTION: [
                    # Обработка текстового ответа
                    MessageHandler(filters.TEXT & ~filters.COMMAND, quiz.handle_quiz_answer),
                    # Обработка кнопок управления викториной
                    CallbackQueryHandler(quiz.handle_quiz_callback,
                                         pattern="^(quiz_continue_|quiz_change_topic|quiz_finish)$")
                ],
            },
            # Возможности выхода из диалога:
            fallbacks=[
                # Команда /start
                CommandHandler("start", basic.start),
                # Нажатие кнопки "main_menu"
                CallbackQueryHandler(basic.menu_callback, pattern="^main_menu$")
            ],
        )

        # Добавление ConversationHandler в приложение:

        # Обработчик викторины
        application.add_handler(quiz_conversation)

        # Обработчик чата с личностью
        application.add_handler(personality_conversation)

        # Обработчик GPT-чата
        application.add_handler(gpt_conversation)

        # Регистрация обработчиков callback-кнопок:

        # Обработчик кнопок случайных фактов (паттерн "random_")
        application.add_handler(CallbackQueryHandler(random_fact.random_fact_callback, pattern="^random_"))

        # Обработчик кнопок рекомендаций (паттерн "recommend_")
        application.add_handler(CallbackQueryHandler(recommendations.recommend_callback, pattern="^recommend_"))

        # Общий обработчик кнопок меню
        application.add_handler(CallbackQueryHandler(basic.menu_callback))

        # Запись в лог об успешном запуске
        logger.info("Бот запущен успешно!")

        # Запуск бота в режиме polling (постоянный опрос сервера Telegram)
        application.run_polling()

    except Exception as e:
        # Запись в лог об ошибке с подробной информацией
        logger.error(f'Ошибка при запуске: {str(e)}', exc_info=True)


# Стандартная проверка для запуска main() при непосредственном выполнении файла
if __name__ == "__main__":
    main()