import os

from celery import shared_task, Celery
from asgiref.sync import async_to_sync

from settings import bot
from database.methods import get_users_ids


app = Celery('background_message', broker=os.getenv('CELERY_BROKER'))


@shared_task
def send_telegram_message(text: str):
    """
    Отправить сообщение всем пользователям
    :param text: текст сообщения
    :return: None
    """
    for user_id in async_to_sync(get_users_ids)():
        bot.send_message(user_id, text)
