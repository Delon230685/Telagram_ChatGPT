# Импорт необходимых модулей
import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.openai_client import get_personality_response
from data.quiz_topics import get_quiz_topics_keyboard, get_quiz_topic_data, get_quiz_continue_keyboard

# Инициализация логгера
logger = logging.getLogger(__name__)

# Определение состояний для ConversationHandler
SELECTING_TOPIC, ANSWERING_QUESTION = range(2)


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /quiz - перенаправляет в quiz_start"""
    logger.info('Обрабатываю нажатие на /quiz')
    await quiz_start(update, context)


async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск интерфейса квиза"""
    try:
        image_path = "data/images/quiz.png"
        logger.info(f'В квизе используется картинка: {image_path}')

        # Текст приветственного сообщения
        message_text = (
            "🧠 <b>Квиз - проверь свои знания!</b>\n\n"
            "Выберите тему для квиза:\n\n"
            "💻 <b>Программирование</b> - вопросы о коде и технологиях\n"
            "🏛️ <b>История</b> - исторические факты и события\n"
            "🔬 <b>Наука</b> - физика, химия, биология\n"
            "🌍 <b>География</b> - страны, столицы, природа\n"
            "🎬 <b>Кино</b> - фильмы и актеры\n\n"
            "Выберите тему:"
        )

        # Получаем клавиатуру с темами квиза
        keyboard = get_quiz_topics_keyboard()

        # Инициализация счетчиков правильных ответов
        if 'quiz_score' not in context.user_data:
            context.user_data['quiz_score'] = 0  # Количество правильных ответов
            context.user_data['quiz_total'] = 0  # Общее количество вопросов

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
            # Обработка обычной команды /quiz
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

        return SELECTING_TOPIC  # Переход в состояние выбора темы

    except Exception as e:
        logger.error(f"Ошибка при запуске квиза: {e}")
        error_text = "😔 Произошла ошибка при запуске квиза. Попробуйте позже."

        if update.callback_query:
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)

        return -1  # Завершение ConversationHandler


async def topic_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора темы квиза"""
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback

    try:
        # Извлекаем ключ темы из callback_data
        topic_key = query.data.replace("quiz_topic_", "")
        # Получаем данные о теме
        topic_data = get_quiz_topic_data(topic_key)

        if not topic_data:
            # Обработка случая, когда тема не найдена
            if query.message.photo:
                await query.edit_message_caption("❌ Ошибка: тема не найдена.")
            else:
                await query.edit_message_text("❌ Ошибка: тема не найдена.")
            return -1

        # Сохраняем выбранную тему в user_data
        context.user_data['current_quiz_topic'] = topic_key
        context.user_data['quiz_topic_data'] = topic_data

        # Отправляем сообщение о генерации вопроса
        processing_text = f"{topic_data['emoji']} Генерирую вопрос по теме {topic_data['name']}... ⏳"
        if query.message.photo:
            await query.edit_message_caption(processing_text, parse_mode='HTML')
        else:
            await query.edit_message_text(processing_text, parse_mode='HTML')

        # Генерируем вопрос с помощью ChatGPT
        question = await get_personality_response("Создай вопрос для квиза", topic_data['prompt'])
        context.user_data['current_question'] = question

        # Извлекаем правильный ответ из текста вопроса
        correct_answer = extract_correct_answer(question)
        context.user_data['correct_answer'] = correct_answer

        # Формируем текст вопроса
        message_text = (
            f"{topic_data['emoji']} <b>Квиз: {topic_data['name']}</b>\n\n"
            f"{question}\n\n"
            f"📊 <b>Счет:</b> {context.user_data['quiz_score']}/{context.user_data['quiz_total']}\n\n"
            "✍️ Напишите ваш ответ (A, B, C или D):"
        )

        # Отправляем вопрос пользователю
        if query.message.photo:
            await query.edit_message_caption(
                caption=message_text,
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                text=message_text,
                parse_mode='HTML'
            )

        return ANSWERING_QUESTION  # Переход в состояние ответа на вопрос

    except Exception as e:
        logger.error(f"Ошибка при выборе темы квиза: {e}")
        try:
            if query.message.photo:
                await query.edit_message_caption("😔 Произошла ошибка при генерации вопроса. Попробуйте еще раз.")
            else:
                await query.edit_message_text("😔 Произошла ошибка при генерации вопроса. Попробуйте еще раз.")
        except Exception:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="😔 Произошла ошибка при генерации вопроса. Попробуйте еще раз."
            )
        return -1


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа пользователя на вопрос квиза"""
    try:
        # Получаем и нормализуем ответ пользователя
        user_answer = update.message.text.strip().upper()
        # Получаем правильный ответ и данные темы
        correct_answer = context.user_data.get('correct_answer', '').upper()
        topic_data = context.user_data.get('quiz_topic_data')
        current_question = context.user_data.get('current_question', '')

        if not topic_data or not correct_answer:
            await update.message.reply_text(
                "❌ Произошла ошибка: данные квиза не найдены. Используйте /quiz для начала."
            )
            return -1

        # Показываем индикатор "печатает"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        # Проверяем правильность ответа
        is_correct = user_answer == correct_answer

        # Обновляем счетчики
        context.user_data['quiz_total'] += 1
        if is_correct:
            context.user_data['quiz_score'] += 1

        # Отправляем сообщение о проверке ответа
        processing_msg = await update.message.reply_text(
            f"{topic_data['emoji']} Проверяю ответ... ⏳"
        )

        # Формируем промпт для анализа ответа
        analysis_prompt = f"""Пользователь ответил '{user_answer}' на вопрос:
        {current_question}

        Правильный ответ: {correct_answer}

        Дай краткое объяснение (2-3 предложения), почему ответ правильный или неправильный, и интересный факт по теме."""

        # Получаем развернутый ответ от ChatGPT
        detailed_response = await get_personality_response(analysis_prompt,
                                                           "Ты эксперт по квизам, объясняешь ответы понятно и интересно.")

        # Формируем текст результата
        if is_correct:
            result_text = f"✅ <b>Правильно!</b>\n\n{detailed_response}"
        else:
            result_text = f"❌ <b>Неправильно!</b>\n\nПравильный ответ: <b>{correct_answer}</b>\n\n{detailed_response}"

        # Получаем клавиатуру для продолжения
        keyboard = get_quiz_continue_keyboard(context.user_data['current_quiz_topic'])

        # Удаляем сообщение о проверке и отправляем результат
        await processing_msg.delete()
        await update.message.reply_text(
            f"{topic_data['emoji']} <b>Результат квиза</b>\n\n"
            f"{result_text}\n\n"
            f"📊 <b>Ваш счет:</b> {context.user_data['quiz_score']}/{context.user_data['quiz_total']}",
            parse_mode='HTML',
            reply_markup=keyboard
        )

        return ANSWERING_QUESTION  # Остаемся в состоянии ответа на вопросы

    except Exception as e:
        logger.error(f"Ошибка при обработке ответа квиза: {e}")
        await update.message.reply_text(
            "😔 Произошла ошибка при проверке ответа. Попробуйте еще раз."
        )
        return ANSWERING_QUESTION


async def handle_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback-кнопок в квизе"""
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback

    try:
        if query.data.startswith("quiz_continue_"):
            # Продолжаем квиз с той же темой
            topic_key = query.data.replace("quiz_continue_", "")
            context.user_data['current_quiz_topic'] = topic_key
            context.user_data['quiz_topic_data'] = get_quiz_topic_data(topic_key)

            # Эмулируем выбор темы для генерации нового вопроса
            fake_query_data = f"quiz_topic_{topic_key}"
            query.data = fake_query_data
            return await topic_selected(update, context)

        elif query.data == "quiz_change_topic":
            # Возвращаем к выбору темы
            return await quiz_start(update, context)

        elif query.data == "quiz_finish":
            # Завершаем квиз и показываем результаты
            score = context.user_data.get('quiz_score', 0)
            total = context.user_data.get('quiz_total', 0)

            # Рассчитываем процент и определяем оценку
            if total > 0:
                percentage = round((score / total) * 100)
                if percentage >= 80:
                    emoji = "🏆"
                    grade = "Отлично!"
                elif percentage >= 60:
                    emoji = "🥈"
                    grade = "Хорошо!"
                elif percentage >= 40:
                    emoji = "🥉"
                    grade = "Неплохо!"
                else:
                    emoji = "📚"
                    grade = "Есть куда расти!"
            else:
                percentage = 0
                emoji = "🤔"
                grade = "Попробуйте еще раз!"

            # Формируем финальное сообщение
            final_text = (
                f"{emoji} <b>Квиз завершен!</b>\n\n"
                f"📊 <b>Финальный результат:</b>\n"
                f"Правильных ответов: {score} из {total}\n"
                f"Процент: {percentage}%\n\n"
                f"<b>{grade}</b>\n\n"
                "Спасибо за участие! 🎉"
            )

            # Очищаем данные квиза
            context.user_data.pop('quiz_score', None)
            context.user_data.pop('quiz_total', None)
            context.user_data.pop('current_quiz_topic', None)
            context.user_data.pop('quiz_topic_data', None)
            context.user_data.pop('current_question', None)
            context.user_data.pop('correct_answer', None)

            # Создаем клавиатуру главного меню
            keyboard = [
                [InlineKeyboardButton("🎲 Случайный факт", callback_data="random_interface")],
                [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_interface")],
                [InlineKeyboardButton("👥 Диалог с личностью", callback_data="talk_interface")],
                [InlineKeyboardButton("🧠 Квиз", callback_data="quiz_interface")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем финальное сообщение
            await query.edit_message_text(
                final_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            return -1  # Завершение ConversationHandler

    except Exception as e:
        logger.error(f"Ошибка в quiz callback: {e}")
        await query.edit_message_text("😔 Произошла ошибка. Попробуйте еще раз.")
        return -1

    return ANSWERING_QUESTION


def extract_correct_answer(question_text):
    """Извлекает правильный ответ из текста вопроса"""
    try:
        lines = question_text.split('\n')
        for line in lines:
            if 'правильный ответ' in line.lower():
                match = re.search(r'[ABCD]', line.upper())
                if match:
                    return match.group()

        match = re.search(r'ответ:\s*([ABCD])', question_text.upper())
        if match:
            return match.group(1)

        return 'A'  # Значение по умолчанию
    except Exception as e:
        logger.error(f"Ошибка при извлечении правильного ответа: {e}")
        return 'A'