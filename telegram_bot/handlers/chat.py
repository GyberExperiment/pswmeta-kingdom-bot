import asyncio
import functools

from telebot import types

from funcs.markups import generate_markup_for_handle_member
from settings import Settings
from funcs.other import delete_message_after_delay
from settings import bot, current_gif_file_id


def chats_only(func):
    @functools.wraps(func)
    async def wrapper(message, *args, **kwargs):
        if message.chat.type != 'private':
            return await func(message, *args, **kwargs)
        else:
            # Вы можете отправить сообщение пользователю, что команда доступна только в ЛС
            await bot.send_message(message.chat.id, 'Эта команда доступна только в личных сообщениях.')
            return
    return wrapper


@bot.chat_member_handler()
@chats_only
async def handle_member(chat_member_updated: types.ChatMemberUpdated):
    """
    Хэндлер пользователей групп телеграма. Тэгает нового пользователя + если есть GIF-файл, то отправляет его с
    приветственным сообщением, если нет - просто приветсвенное. Сообщение удаляется через 900 сек. С логгированием
    :param chat_member_updated:
    :return:
    """
    if chat_member_updated.new_chat_member.status == 'member':
        if chat_member_updated.chat.type in ['group', 'supergroup']:
            # Клавиатура для ответа
            markup = await generate_markup_for_handle_member(bot)

            # текст с именем пользователя ТГ
            mention = f"@{chat_member_updated.new_chat_member.user.username}" \
                if chat_member_updated.new_chat_member.user.username \
                else f"@{chat_member_updated.new_chat_member.user.first_name}"

            if current_gif_file_id != "DEFAULT_FILE_ID":
                answer_message = await bot.send_animation(
                    chat_id=chat_member_updated.chat.id,
                    animation=current_gif_file_id,
                    caption=f'{mention}\n\n{Settings.CURRENT_WELCOME_MESSAGE}',
                    reply_markup=markup
                )
            else:
                answer_message = await bot.send_message(
                    chat_id=chat_member_updated.chat.id,
                    text=f'{mention}\n\n{Settings.CURRENT_WELCOME_MESSAGE}',
                    reply_markup=markup
                )
            # Создание таски с удалением сообщения через 900 сек
            await asyncio.create_task(delete_message_after_delay(chat_member_updated.chat.id,
                                                                 answer_message.message_id))
