import time
from sqlalchemy import func, desc
from sqlalchemy.orm import aliased
from sqlalchemy import select

from backend import Backend
from database.models import UserTasks, RewardsTime, TelegramUser
from database.main import get_session
from database.models import Users, UserReferrals
from funcs.markups import users_menu_keyboard
from settings import bot


async def get_user_referrals(user_id):
    async with get_session() as session:
        result = await session.execute(select(UserReferrals).where(UserReferrals.referrer_id == user_id))  # noqa

        return [row.user_id for row in result.scalars().all()]


async def get_all_user_tasks():
    """
    Получить все задания для пользователей.

    :return: Список заданий.
    """
    async with get_session() as session:
        result = await session.execute(select(UserTasks))

        return result.scalars().all()


async def add_task(description, task_type, chat_id=None, chat_link='', reward=0):
    """
    Добавить задание для пользователя.

    :param description: Описание задания.
    :param task_type: Тип задания.
    :param chat_id: ID чата.
    :param chat_link: Ссылка на чат.
    :param reward: Награда за задание.
    :return: Задание.
    """
    async with get_session() as session:
        task = UserTasks(description=description, task_type=task_type, chat_id=chat_id,
                         chat_link=chat_link, reward=reward)

        session.add(task)
        await session.commit()

        return task


async def remove_task(task_id):
    """
    Удалить задание.

    :param task_id: ID задания.
    :return: True, если задание удалено, False в противном случае.
    """
    async with get_session() as session:
        result = await session.execute(select(UserTasks).where(UserTasks.id == task_id))  # noqa


async def write_last_update_time(timestamp):
    """
    Записывает время последнего обновления балансов в базу данных.

    :param timestamp: время последнего обновления балансов
    :return: None
    """
    async with get_session() as session:
        result = await session.execute(select(RewardsTime).limit(1))

        last_update_time = result.scalar_one_or_none()

        if not last_update_time:
            last_update_time = RewardsTime(last_referrals_time=timestamp, last_update_time=int(time.time()))

            session.add(last_update_time)
        else:
            last_update_time.last_referrals_time = timestamp

        await session.commit()
        await session.refresh(last_update_time)


async def read_last_update_time():
    """
    Читает время последнего обновления балансов из базы данных.

    :return: время последнего обновления балансов, или текущее время, если запись не найдена
    """
    async with get_session() as session:
        result = await session.execute(select(RewardsTime).limit(1))

    last_update_time = result.scalar_one_or_none()

    if not last_update_time:
        return int(time.time())

    return last_update_time.last_referrals_time


async def get_users_info():
    """
    Получить информацию о пользователях.

    :return: Количество пользователей и рефералов.
    """
    async with get_session() as session:
        result = await session.execute(select(Users))

        users_count = len(result.scalars().all())

        total_referrals_result = await session.execute(
            select(func.count(UserReferrals.user_id))
        )
        total_referrals = total_referrals_result.scalar() or 0

        referral_count_alias = aliased(
            select(
                UserReferrals.referrer_id,
                func.count(UserReferrals.user_id).label('referral_count')
            )
            .group_by(UserReferrals.referrer_id)
            .subquery()
        )

        result = await session.execute(
            select(Users, referral_count_alias.c.referral_count)
            .join(
                referral_count_alias,
                referral_count_alias.c.referrer_id == Users.user_id,
                isouter=True
            )
            .order_by(desc(referral_count_alias.c.referral_count))
            .limit(5)
        )

        top_users = [
            {"user_id": user.user_id, "user_name": user.user_name, "referral_count": referral_count or 0}
            for user, referral_count in result.all()
        ]

        return users_count, top_users, total_referrals


async def get_user_info(user_id):
    """
    Получить информацию о пользователе.

    :param user_id: ID пользователя.
    :return: Информация о пользователе.
    """
    async with get_session() as session:
        result = await session.execute(select(UserReferrals).where(UserReferrals.user_id == user_id))  # noqa

        user = result.scalars().one()

        if not user:
            return None

        result = await session.execute(select(UserReferrals).where(UserReferrals.referrer_id == user_id))  # noqa

        referrals_count = len(result.scalars().all())

        return user, referrals_count


async def add_user_with_referral_check(message):
    async with get_session() as session:
        # Получение информации о юзере с backend'а
        handled_user_data = await Backend.handle_user(message.from_user.id)

        # Запрос к БД на получение того, кто пригласил юзера
        referral_user_exists = await session.execute(
            select(UserReferrals).where(UserReferrals.user_id == message.from_user.id))  # noqa

        # Получение данных о том, кто пригласил
        referral_user = referral_user_exists.scalar_one_or_none()

        # Если приглашённый
        if not referral_user:
            # Если от бэкенда пришёл ответ 'created'
            if handled_user_data['status'] == 'created':
                # Получение id реферала(вроде диплинк называется, когда после /start пишется текст, которй не виден
                # юзеру тг
                referrer_id = message.text.split()[1] if len(message.text.split()) > 1 else None

                # Если есть ID, то ему добавляется реферал
                if referrer_id:
                    await Backend.add_referral(message.from_user.id, int(referrer_id))

            # Если от бэкенда пришёл ответ 'exists'. Хотя, по идее, если пользователь уже зарегистрирован, он не
            # может стать рефералом
            elif handled_user_data['status'] == 'exists':
                referrer_id = message.text.split()[1] if len(message.text.split()) > 1 else None

                if referrer_id:
                    await Backend.add_referral(message.from_user.id, int(referrer_id))

        await bot.send_message(message.chat.id, 'Loading the user menu...', reply_markup=users_menu_keyboard())

        # Получение класса TelegramUser из БД
        user_exists = await session.execute(select(TelegramUser).
                                            where(TelegramUser.user_id == message.from_user.id))  # noqa
        user = user_exists.scalar_one_or_none()

        # Если пользователя нет - он добавляется бд
        if user is None or not user:
            tg_user = TelegramUser(user_id=message.from_user.id, chat_id=message.chat.id)

            session.add(tg_user)
            await session.commit()

async def get_users_ids():
    """
    Получить ID всех пользователей.
    :return:
    """
    async with get_session() as session:
        result = await session.execute(select(TelegramUser.user_id))

        return result.scalars().all()
