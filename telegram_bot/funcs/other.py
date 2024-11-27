import asyncio
import logging
import time

from settings import bot, user_referrals_requests, TIME_WINDOW_REFERRALS, MAX_REFERRALS_REQUESTS, user_requests, \
    TIME_WINDOW, MAX_REQUESTS


async def delete_message_after_delay(chat_id, message_id):
    """
    Удалить сообщение после задержки.

    :param chat_id: ID чата.
    :param message_id: ID сообщения.
    """
    try:
        await asyncio.sleep(900)

        await bot.delete_message(chat_id, message_id)

        logging.info(f'Message {message_id} in chat {chat_id} was deleted after 15 minutes.')
    except Exception as e:
        logging.error(f'Error while deleting message {message_id}: {e}')


def is_referrals_rate_limited(user_id):
    """
    Проверить, превышен ли лимит рефералов для пользователя.

    :param user_id: ID пользователя.
    :return: True, если лимит превышен, False в противном случае.
    """
    now = time.time()

    requests = user_referrals_requests[user_id]

    requests = [req_time for req_time in requests if now - req_time < TIME_WINDOW_REFERRALS]

    if len(requests) >= MAX_REFERRALS_REQUESTS:
        return True

    requests.append(now)

    user_referrals_requests[user_id] = requests

    return False


async def get_username_by_user_id(user_id):
    """
    Получить имя пользователя по его ID.

    :param user_id: ID пользователя.
    :return: Имя пользователя.
    """
    try:
        user = await bot.get_chat(user_id)

        return "@" + user.username if user.username else user.first_name
    except Exception as e:
        logging.error(f'Error getting username for user_id {user_id}: {e}')

        return None


def is_rate_limited(user_id):
    """
    Проверяет, превышен ли лимит запросов для пользователя с указанным user_id.

    :param user_id: идентификатор пользователя
    :return: True, если лимит запросов превышен, иначе False
    """
    now = time.time()

    requests = user_requests[user_id]

    requests = [req_time for req_time in requests if now - req_time < TIME_WINDOW]

    if len(requests) >= MAX_REQUESTS:
        return True

    requests.append(now)

    user_requests[user_id] = requests

    return False


async def check_tag_in_name(chat_id, user_id):
    """
    Проверяет, содержит ли имя пользователя с указанным user_id в чате с chat_id тег "PSWMeta".

    :param chat_id: идентификатор чата
    :param user_id: идентификатор пользователя
    :return: True, если тег найден, иначе False
    """
    try:
        chat_member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)

        user_first_name = chat_member.user.first_name if chat_member.user.first_name else ""
        user_last_name = chat_member.user.last_name if chat_member.user.last_name else ""

        if "PSWMeta" in user_first_name or "PSWMeta" in user_last_name:
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error while checking tag in name: {e}")

        return False
