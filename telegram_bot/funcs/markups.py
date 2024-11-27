from telebot import types
from settings import Settings


async def generate_markup_for_handle_member(bot):
    markup = types.InlineKeyboardMarkup()
    bot_me = await bot.get_me()
    markup.add(types.InlineKeyboardButton(text='🚀 Start APP', url=f't.me/{bot_me.username}'))
    markup.row(
        types.InlineKeyboardButton(text='🌐 X', url='https://x.com/powerswapmeta'),
        types.InlineKeyboardButton(text='📢 Channel', url='https://t.me/powerswapmeta')
    )
    markup.row(
        types.InlineKeyboardButton(text='💬 Group', url='https://t.me/powerswapmetagroup'),
        types.InlineKeyboardButton(text='🔗 Gybernaty', url='https://gyber.org')
    )
    return markup


async def generate_markup_for_send_welcome_to_user():
    markup = types.InlineKeyboardMarkup()
    web_url = types.WebAppInfo(Settings.APP_REFERRALS_URL)
    markup.add(types.InlineKeyboardButton(text='🚀 Start APP', web_app=web_url))
    markup.row(
        types.InlineKeyboardButton(text='🌐 X', url='https://x.com/powerswapmeta'),
        types.InlineKeyboardButton(text='📢 Channel', url='https://t.me/powerswapmeta')
    )
    markup.row(
        types.InlineKeyboardButton(text='💬 Group', url='https://t.me/powerswapmetagroup'),
        types.InlineKeyboardButton(text='🔗 Gybernaty', url='https://gyber.org')
    )
    return markup


async def generate_markup_for_admin_panel():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Set Welcome Message', callback_data='set_welcome_message'))
    markup.add(types.InlineKeyboardButton(text='Set Welcome GIF', callback_data='set_welcome_gif'))
    markup.add(types.InlineKeyboardButton(text='Get Users Info', callback_data='get_users_info'))
    markup.add(types.InlineKeyboardButton(text='Get User Info', callback_data='get_user_info'))
    markup.add(types.InlineKeyboardButton(text='Get Users Tasks', callback_data='get_users_tasks'))
    markup.add(types.InlineKeyboardButton(text='Add Users Task', callback_data='add_users_task'))
    markup.add(types.InlineKeyboardButton(text='Delete Users Task', callback_data='delete_users_task'))
    return markup


def users_menu_keyboard():
    """
    Клавиатура меню для пользователей.

    :return: Клавиатура меню.
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add(types.KeyboardButton('♻ Tasks'))
    keyboard.add(types.KeyboardButton('🚸 Referrals'))

    return keyboard
