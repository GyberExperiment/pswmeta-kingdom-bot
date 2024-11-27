import time
import asyncio
import logging
import random

from sqlalchemy import select

from database.main import get_session
from backend import Backend
from database.models import TelegramUser
from database.methods import read_last_update_time, write_last_update_time
from messages import messages
from funcs.other import check_tag_in_name
from settings import MAIN_CHAT_ID


async def update_balances(bot):
    """
    Асинхронная функция, которая обновляет балансы пользователей каждые 3 часа.

    :return: None
    """
    await asyncio.sleep(20)

    interval = 10800

    last_update_time = await read_last_update_time()

    logging.info(f"Last adding rewards time: {last_update_time}")

    while True:
        current_time = time.time()
        time_since_last_update = current_time - last_update_time

        if time_since_last_update >= interval:
            logging.info(f"Start adding rewards for users")

            try:
                async with get_session() as session:
                    success, users = await Backend.increase_balance_for_referrers()

                    if success:
                        logging.info(f'Successfully increased balances for referrers: {success}')

                        users_raw = await session.execute(select(TelegramUser))
                        users_orm = users_raw.scalars().all()

                        telegram_users = {user.user_id: user.chat_id for user in users_orm}

                        for user in users:
                            try:
                                if user[0] not in telegram_users:
                                    continue

                                if telegram_users[user[0]] == MAIN_CHAT_ID:
                                    logging.warning(f"Skipped user {key} with chat MAIN_CHAT_ID")

                                    continue

                                message = random.choice(messages)

                                await bot.send_message(telegram_users[user[0]], message.format(points=user[1]))
                            except Exception as e:
                                logging.error(f'Error while sending message to user {user[0]}: {e}')

                        logging.info(f'Starting increase balances for prefix...')

                        points_for_prefix = 10000
                        users_to_increase = []

                        for key, value in telegram_users.items():
                            if value == MAIN_CHAT_ID:
                                logging.warning(f"Skipped user {key} with chat MAIN_CHAT_ID")

                                continue

                            try:
                                has_prefix = await check_tag_in_name(MAIN_CHAT_ID, key)

                                if has_prefix:
                                    users_to_increase.append(key)

                                    await bot.send_message(value,
                                                           f'🎉 <b>You earned {points_for_prefix} '
                                                           f'$PSWMeta points for the tag in your nickname!</b>')

                                await asyncio.sleep(0.05)
                            except Exception as e:
                                logging.error(f'Error while checking tag in name for user {key}: {e}')

                        if users_to_increase:
                            if await Backend.increase_balance_for_prefix(users_to_increase):
                                logging.info(f'Increasing balances for prefix... count: {len(users_to_increase)}')

                    last_update_time = time.time()

                    await write_last_update_time(last_update_time)
            except Exception as e:
                logging.error(f'Error while updating balances: {e}')

                await asyncio.sleep(interval)
        else:
            logging.info(f"Waiting for adding rewards: {interval - time_since_last_update}")

            await asyncio.sleep(interval - time_since_last_update)