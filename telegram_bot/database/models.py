from database.main import Base

from sqlalchemy import Column, BigInteger, Integer, String, JSON, ARRAY


class Users(Base):
    __tablename__ = "users_v1"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(BigInteger, unique=True, index=True)
    user_name = Column(String(255), index=True, default="")

    tokens_amount = Column(BigInteger, default=0)
    referrals_tokens_amount = Column(BigInteger, default=0)

    game_information = Column(JSON, default={
        'current_level': 0,
        'tap_multiplier': 1
    })

    resources_amount = Column(JSON, default={
        'crypto': {
            'value': 0,
        },
        'heat': {
            'value': 0,
        },
        'energy': {
            'value': 0,
        },
        'food': {
            'value': 0,
        },
    })

    upgrades_information = Column(JSON, default={
        'miner': {
            'level': 0,
            'multiplier': 1
        },
        'grower': {
            'level': 0,
            'multiplier': 1
        },
        'power plant': {
            'level': 0,
            'multiplier': 1
        }
    })

    state = Column(JSON, default={
        'last_active_resource': 0,
        'last_opened_page': 0
    })


class TelegramUser(Base):
    __tablename__ = 'telegram_users'

    id = Column(BigInteger, primary_key=True)

    user_id = Column(BigInteger, unique=True, index=True)
    chat_id = Column(BigInteger, unique=True, index=True)

    completed_tasks_chat_ids = Column(ARRAY(BigInteger), default=[])
    completed_tasks_other_types = Column(ARRAY(String(255)), default=[])


class UserReferrals(Base):
    __tablename__ = 'user_referrals_v1'

    id = Column(BigInteger, primary_key=True)

    user_id = Column(BigInteger, index=True)
    referrer_id = Column(BigInteger, index=True)


class UserTasks(Base):
    __tablename__ = 'user_tasks_v1'

    id = Column(BigInteger, primary_key=True)

    description = Column(String(255))

    task_type = Column(String(255))

    chat_id = Column(BigInteger)
    chat_link = Column(String(255), default=None)

    reward = Column(BigInteger, default=0)


class RewardsTime(Base):
    __tablename__ = 'rewards_time_v1'

    id = Column(BigInteger, primary_key=True)

    last_referrals_time = Column(BigInteger)
    last_game_time = Column(BigInteger)
