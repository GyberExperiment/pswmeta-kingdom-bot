import functools
import logging
import asyncio

import telebot.types
from telebot import util

from settings import bot, privileged_users_id

from database.main import init_models
from funcs.states import set_user_state, get_user_state, clear_user_state
from database.methods import add_task, remove_task, get_user_info

# По идее, этот импорт должен инициализировать хэндлеры
import handlers     # noqa


logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)


# оставил тут, тк это обработка сообщений, которые не прошли предыдущих хэндлеров и это должно быть в конце :)
@bot.message_handler()
async def handle_text_messages(message):
    """
    Тут происходит все обновления силами админа. Проверяется статус самого админа и производяться действия, в
    соответсвии со статусами
    :param message:
    :return:
    """
    if message.from_user.id not in privileged_users_id:
        return

    if get_user_state(message.from_user.id) == 'get_user_info':
        clear_user_state(message.from_user.id)

        try:
            user_id = int(message.text)

            user_info = await get_user_info(user_id)

            if user_info:
                user, referrals_count = user_info

                await bot.send_message(message.chat.id,
                                       f'User ID: {user.user_id}\nReferrals: {referrals_count}')
            else:
                await bot.send_message(message.chat.id, 'User not found.')
        except Exception as e:
            logging.error(f'Invalid user ID: {e}')

            await bot.send_message(message.chat.id, 'Invalid user ID. Please try again.')

    elif get_user_state(message.from_user.id) == 'add_users_task':
        try:
            task_description = message.text

            set_user_state(message.from_user.id, 'add_users_task_chat_id', value={
                'description': task_description
            })

            await bot.send_message(message.chat.id,
                                   f'Please send the chat ID for the task you want to add')
        except Exception as e:
            logging.error(f'Error adding task: {e}')

            await bot.send_message(message.chat.id,
                                   'Error adding task. Please try again.')

    elif get_user_state(message.from_user.id) == 'add_users_task_chat_id':
        try:
            try:
                chat_id = int(message.text)

            except ValueError:
                await bot.send_message(message.chat.id, 'Invalid chat ID. Please try again.')

                return

            task_data = get_user_state(message.from_user.id, include_value=True)[1]

            task_data['chat_id'] = chat_id

            set_user_state(message.from_user.id, 'add_users_task_chat_link', value=task_data)

            await bot.send_message(message.chat.id,
                                   f'Please send the chat link for the task you want to add (example: @powerswapmeta)')

        except Exception as e:
            logging.error(f'Error adding task: {e}')

    elif get_user_state(message.from_user.id) == 'add_users_task_chat_link':
        try:
            chat_link = message.text

            task_data = get_user_state(message.from_user.id, include_value=True)[1]

            task_data['chat_link'] = chat_link

            set_user_state(message.from_user.id, 'add_users_task_reward', value=task_data)

            await bot.send_message(message.chat.id, f'Please send the reward for the task you want to add')

        except Exception as e:
            logging.error(f'Error adding task: {e}')

    elif get_user_state(message.from_user.id) == 'add_users_task_reward':
        try:
            task_data = get_user_state(message.from_user.id, include_value=True)[1]

            try:
                reward = int(message.text)
            except ValueError:
                await bot.send_message(message.chat.id, 'Invalid reward. Please try again.')

                return

            task_data['reward'] = reward

            logging.info(f'Adding task: {task_data}')

            task = await add_task(task_data['description'], 'join_channel',
                                  task_data['chat_id'], task_data['chat_link'], task_data['reward'])

            await bot.send_message(message.chat.id, f'Task added successfully with ID: {task.id}')
        except Exception as e:
            logging.error(f'Error adding task: {e}')

            clear_user_state(message.from_user.id)

            await bot.send_message(message.chat.id, 'Error adding task. Please try again.')

        clear_user_state(message.from_user.id)

    elif get_user_state(message.from_user.id) == 'remove_users_task':
        clear_user_state(message.from_user.id)

        try:
            task_id = int(message.text)

            if await remove_task(task_id):
                await bot.send_message(message.chat.id, f'Task with ID {task_id} removed successfully.')
            else:
                await bot.send_message(message.chat.id, f'Task with ID {task_id} not found.')
        except Exception as e:
            logging.error(f'Invalid task ID: {e}')

            await bot.send_message(message.chat.id, 'Invalid task ID. Please try again.')


async def on_startup():
    try:
        await init_models()
    except Exception as e:
        logging.error(f'Error while initializing models: {e}')

    # await asyncio.create_task(update_balances())

    logging.info('Telegram bot started!')
    await bot.infinity_polling(allowed_updates=util.update_types, skip_pending=True)


if __name__ == '__main__':
    asyncio.run(on_startup())
