import asyncio
import logging

from sqlalchemy import select
from telebot import types

from database.main import get_session
from database.models import TelegramUser, Users
from funcs.markups import generate_markup_for_send_welcome_to_user

from messages import presale_text, contract_address_text
from settings import Settings
import functools
from funcs.ai import get_langchain_response
from funcs.other import is_referrals_rate_limited, get_username_by_user_id, is_rate_limited, check_tag_in_name


from settings import bot, chat_history, MAIN_CHAT_ID

from database.methods import get_user_referrals, get_all_user_tasks, add_user_with_referral_check


def private_chat_only(func):
    @functools.wraps(func)
    async def wrapper(message, *args, **kwargs):
        if message.chat.type == 'private':
            return await func(message, *args, **kwargs)
        else:
            # Вы можете отправить сообщение пользователю, что команда доступна только в ЛС
            await bot.send_message(message.chat.id, 'Эта команда доступна только в личных сообщениях.')
            return
    return wrapper


@bot.message_handler(commands=['presale'])
@private_chat_only
async def handle_presale_info(message):
    """
    Отправляет ссылку на игру
    :param message:
    :return:
    """

    await bot.send_message(message.chat.id, presale_text, parse_mode='HTML', disable_web_page_preview=True)


@bot.message_handler(commands=['ca'])
@private_chat_only
async def handle_contract_address_info(message):
    """
    Отправляет сообщение с ссылкой на contract addresses (какая-то криптобиржа)
    :param message:
    :return:
    """
    await bot.send_message(message.chat.id, contract_address_text, parse_mode='HTML', disable_web_page_preview=True)


@bot.message_handler(commands=['ai'])
@private_chat_only
async def handle_ai_command(message):
    """
    Хэндлер для обработки запросов к AI
    :param message:
    :return:
    """
    # Запрос к AI
    query = message.text.replace('/ai', '').strip()

    # Проверка был ли уже диалог с AI, если нет, то создаётся пара {user.id: []}
    if message.from_user.id not in chat_history:
        chat_history[message.from_user.id] = []

    # Если запроса после команды не было, то отправляется информационное сообщение
    if not query:
        await bot.send_message(message.chat.id, 'Please enter a question after the /ai command.')

        return

    try:
        # Обращение к AI в отдельном потоке
        response = await asyncio.to_thread(get_langchain_response, query, chat_history[message.from_user.id])

        # Обновление истории переписки
        chat_history[message.from_user.id].append(("Human: " + query, "Assistant: " + response))

        await bot.reply_to(message, response, parse_mode='HTML')

    except Exception as e:
        logging.error(f'Error while processing AI request: {e}')

        await bot.send_message(message.chat.id,
                               'An error occurred while processing your request. Please try again later.')


@bot.message_handler(commands=['start'])
@private_chat_only
async def send_welcome_to_user(message):
    """

    :param message:
    :return:
    """
    markup = await generate_markup_for_send_welcome_to_user()
    try:
        await add_user_with_referral_check(message)

        await bot.send_message(message.chat.id, Settings.CURRENT_WELCOME_MESSAGE, reply_markup=markup)

    except Exception as e:
        logging.error(f'Error while sending welcome message: {e}')

        await bot.send_message(message.chat.id,
                               'Oops! An error occurred while sending the welcome message. Please try again later.')


@bot.message_handler(func=lambda message: message.text == '♻ Tasks')
@private_chat_only
async def show_tasks(message):
    """
    Хэндер команды ♻ Tasks. Возвращает таски
    :param message:
    :return:
    """
    try:
        await show_user_tasks(message)
    except Exception as e:
        logging.error(f'Error in show user messages: {e}')

        await bot.send_message(message.chat.id,
                               'Oops! An error occurred while sending the welcome message. Please try again later.')


@bot.message_handler(func=lambda message: message.text == '🚸 Referrals')
@private_chat_only
async def show_user_referrals(message):
    """
    Показать рефералов
    :param message:
    :return:
    """
    try:
        user_id = message.from_user.id

        # Проверка на частоту запросов рефералов
        if is_referrals_rate_limited(user_id):
            return await bot.send_message(message.chat.id, 'Rate limit exceeded. Please try again later.')

        # Дальше получается информация о рефералах из БД
        referrals = await get_user_referrals(user_id)

        if not referrals:
            await bot.send_message(message.chat.id, 'No referrals found.')
        else:
            usernames = []

            await bot.send_message(message.chat.id, 'Loading you referrals...')

            for referral_id in referrals:
                username = await get_username_by_user_id(referral_id)

                if username:
                    usernames.append(username)

                await asyncio.sleep(0.1)

            if usernames:
                await bot.send_message(message.chat.id, f'Your referrals: {", ".join(usernames)}')
            else:
                await bot.send_message(message.chat.id, 'No usernames found for your referrals.')

    except Exception as e:
        logging.error(f'Error getting referrals: {e}')

        await bot.send_message(message.chat.id,
                               'An error occurred while trying to get your referrals. Please try again later.')


async def show_user_tasks(message):
    """
    Сообщение о тасках пользователя, если он есть в БД
    :param message:
    :return:
    """
    tasks = await get_all_user_tasks()

    if not tasks:
        await bot.send_message(message.chat.id, 'No tasks found.')

        return

    async with get_session() as session:
        user = await session.execute(select(TelegramUser).where(TelegramUser.user_id == message.from_user.id))  # noqa

        user = user.scalar_one_or_none()

        if not user:
            await bot.send_message(message.chat.id, "Sorry, can not find you in our base, send '/start' before")

            return

    user_tasks = ''

    user_completed_tasks = set(user.completed_tasks_chat_ids)

    for task in tasks:
        if task.chat_id in user_completed_tasks:
            user_tasks += (f"Task Status: Completed ✅\n - Join to: {task.chat_link}\n "
                           f"- Reward: ${task.reward} PSWMeta points!\n\n")
        else:
            user_tasks += (f"Task Status: In process 🔎\n - Join to: {task.chat_link}\n "
                           f"- Reward: ${task.reward} PSWMeta points!\n\n")

    if await check_tag_in_name(MAIN_CHAT_ID, user.user_id):
        user_tasks += f"Tag 'PSWMeta' status: Added ✅\n - Reward: $10000 PSWMeta points every 3 hours"
    else:
        user_tasks += f"Tag 'PSWMeta' status: Not added ❎\n - Reward: $10000 PSWMeta points every 3 hours"

    inline_keyboard = types.InlineKeyboardMarkup()

    inline_keyboard.add(types.InlineKeyboardButton('❓ Check', callback_data='check_user_tasks'))

    await bot.send_message(message.chat.id, user_tasks, reply_markup=inline_keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ['check_user_tasks'])
@private_chat_only
async def handle_user_check_tasks(call):
    """
    Обработка нажатия на кнопку "❓ Check". Возвращает таски пользователя или сообщение о превышение лимита на запросы
    :param call:
    :return:
    """
    try:
        # Если посылает этот запрос слишком часто
        if is_rate_limited(call.from_user.id):
            return await bot.answer_callback_query(call.id, text="Too many requests. Please try again later.")

        async with get_session() as session:
            user_exists = await session.execute(select(TelegramUser).
                                                where(TelegramUser.user_id == call.from_user.id))   # noqa

            user = user_exists.scalar_one_or_none()

            if not user:
                return await bot.answer_callback_query(call.id, text="Sorry, I can't find you in our base, "
                                                                     "try to send '/start'!")

            completed_tasks = list(user.completed_tasks_chat_ids)

            tasks = await get_all_user_tasks()

            points_reward = 0

            for task in tasks:
                if task.chat_id in completed_tasks:
                    continue

                points_reward += task.reward

                completed_tasks.append(task.chat_id)

            user.completed_tasks_chat_ids = completed_tasks

            if points_reward > 0:
                full_user_exists = await session.execute(select(Users).
                                                         where(Users.user_id == call.from_user.id))     # noqa

                full_user = full_user_exists.scalar_one_or_none()

                if full_user:
                    full_user.referrals_tokens_amount += points_reward

                await session.commit()
                await session.refresh(user)

                if full_user:
                    await session.refresh(full_user)

        await bot.answer_callback_query(call.id,
                                        text=f'👑 You earned it for the tasks: ${points_reward} PSWMeta points!')
    except Exception as e:
        logging.error(f'Error handling user check tasks: {e}')

        await bot.answer_callback_query(call.id, text='Error occurred, please try again.')
