import re
from datetime import timedelta

from celery_task import send_telegram_message
from funcs.markups import generate_markup_for_admin_panel
from funcs.states import set_user_state
from database.methods import get_users_info, get_all_user_tasks
import settings
from settings import Settings
from settings import bot, privileged_users_id


@bot.callback_query_handler(func=lambda call: call.data in [
    'set_welcome_message', 'set_welcome_gif', 'get_users_info',
    'get_user_info', 'get_users_tasks', 'add_users_task', 'delete_users_task'
])
async def handle_admin_callbacks(call):
    """
    Обработка callback'ов с кнопок в админ-панели
    :param call:
    :return:
    """
    # Проверка на привелегии пользователя
    if call.from_user.id in privileged_users_id:
        if call.data == 'set_welcome_message':
            await bot.send_message(call.message.chat.id,
                                   'Please send the new welcome message using the command /set_welcome_message your_message.')  # noqa

        elif call.data == 'set_welcome_gif':
            await bot.send_message(call.message.chat.id,
                                   'Please send the new welcome GIF by uploading it to this chat.')

        elif call.data == 'get_users_info':
            # TODO: сомнительная вещь. Возвращает инфу о пользователях + его рефералах. То есть может быть мега-огромное
            # сообщение
            users_count, top_users, total_referrals = await get_users_info()

            top_users_text = "\n".join(
                f"{idx + 1}. {user['user_name']} (ID: {user['user_id']}) - {user['referral_count']} referrals"
                for idx, user in enumerate(top_users)
            )

            message_text = (
                f"Total users: {users_count}\n"
                f"Top by referrals:\n{top_users_text}"
                f"Referrals:\n{total_referrals}"
            )

            await bot.send_message(call.message.chat.id, message_text)

        elif call.data == 'get_user_info':
            '''
            Обновляет статус пользователя пошагово: нажатие админом на кнопку -> отправление админом ID нужного 
            пользователя -> новый статус пользователя
            Для произведения всех этих шагов используется словарь privileged_user_states вместо state-менеджера
            '''
            await bot.send_message(call.message.chat.id,
                                   'Please send the user ID for which you want to get the info.')

            set_user_state(call.from_user.id, 'get_user_info')

        elif call.data == 'get_users_tasks':
            # TODO: опять мегаогромное сообщение
            # Возвращает таски всех пользователей
            all_tasks = await get_all_user_tasks()

            message = 'All Tasks:\n\n'

            if not all_tasks:
                await bot.send_message(call.message.chat.id, 'No tasks found.')
            else:
                for task in all_tasks:
                    message += (f'Task ID: {task.id}\nChat ID: {task.chat_id}\n'
                                f'Chat link: {task.chat_link}\nDescription: {task.description}\n\n')

            await bot.send_message(call.message.chat.id, message)

        elif call.data == 'add_users_task':
            # Пошаговое добавление таски пользователю
            await bot.send_message(call.message.chat.id,
                                   'Please send the description of the task you want to add.')

            set_user_state(call.from_user.id, 'add_users_task')

        elif call.data == 'delete_users_task':
            # Пошаговое удаление таски пользователя
            await bot.send_message(call.message.chat.id,
                                   'Please send the task ID you want to delete.')

            set_user_state(call.from_user.id, 'remove_users_task')


@bot.message_handler(commands=['set_welcome_message'])
async def set_welcome_message(message):
    """
    Админская функцая, в которой можно задать своё привественное сообщение
    :param message:
    :return:
    """
    if message.from_user.id in privileged_users_id:
        new_message = message.text.replace('/set_welcome_message', '').strip()
        Settings.CURRENT_WELCOME_MESSAGE = new_message

        await bot.send_message(message.chat.id,
                               f'Welcome message has been updated successfully, now welcome message is {new_message}')


@bot.message_handler(content_types=['animation'])
async def set_welcome_gif(message):
    """
    Админская функцая, в которой можно задать новый gif_file
    :param message:
    :return:
    """
    if message.from_user.id in privileged_users_id:
        new_gif_file_id = message.animation.file_id
        settings.current_gif_file_id = new_gif_file_id

        await bot.send_message(message.chat.id, 'Welcome GIF has been updated successfully!')


@bot.message_handler(commands=['admin'])
async def admin_panel(message):
    """
    Возвращает admin-панель
    :param message:
    :return:
    """
    if message.from_user.id in privileged_users_id:
        markup = await generate_markup_for_admin_panel()

        await bot.send_message(message.chat.id, 'Admin Panel', reply_markup=markup)


@bot.message_handler(commands=['distribute'])
async def admin_distribute(message):
    """
    Админская функция для рассылки сообщений пользователям
    :param message:
    :return
    """
    if message.from_user.id in privileged_users_id:
        data = message.text.replace('/distribute ', '')
        if re.match(r'\d\d:\d\d \d\d\n[\s\S]+', data):
            text = data.split('\n')[1:]
            time = data.split('\n')[0]
            minutes = time.split(':')[0]
            hours = time.split(':')[1].split(' ')[0]
            days = time.split(':')[1].split(' ')[1]

            delta = timedelta(minutes=float(minutes),
                              hours=float(hours),
                              days=float(days))

            send_telegram_message.apply_async(eta=delta, args=text)

        else:
            await bot.send_message('Введите через какой промежуток времени начать рассылку\n\n'
                                   'Формат: \n\n/distibute mm:hh d\nВАШ ТЕКСТ ЗДЕСЬ')
