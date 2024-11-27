import logging
import aiohttp

from settings import Settings


class Backend:
    """
    Класс, который предоставляет методы для взаимодействия с сервером API backend'а.

    """

    session = None

    @classmethod
    async def init_session(cls):
        """
        Инициализирует сессию aiohttp, если она еще не была инициализирована.

        :return: None
        """
        if cls.session is None:
            client_timeout = aiohttp.ClientTimeout(total=120)

            cls.session = aiohttp.ClientSession(base_url=Settings.COMMUNICATION_BASE_URL, timeout=client_timeout)

    @staticmethod
    async def get_user_by_id(user_id: int) -> dict | None:
        """
        Получает информацию о пользователе по его идентификатору.

        :param user_id: идентификатор пользователя
        :return: словарь с информацией о пользователе, или None, если запрос не удался
        """
        try:
            await Backend.init_session()

            headers = {
                'x-admin-key': Settings.ADMIN_KEY
            }

            async with Backend.session.get(f'/api/v1/users/get/{user_id}', headers=headers) as response:
                response.raise_for_status()

                if response.status == 200:
                    data = await response.json()

                    return data['data']

            return None
        except Exception as e:
            logging.error(f'Error getting user: {e}')

            return None

    @staticmethod
    async def handle_user(user_id: int) -> dict | None:
        """
        Добавляет пользователя в базу данных.

        :param user_id: идентификатор пользователя
        :return: словарь с информацией о статусе обработки пользователя
        """
        ret = {'status': 'unknown'}

        try:
            await Backend.init_session()

            headers = {
                'x-api-key': Settings.API_KEY
            }

            async with Backend.session.post('/api/v1/users/create', json={'user_id': user_id},
                                            headers=headers) as post_response:
                response = post_response

            if response.status == 200:
                ret['status'] = 'created'
            elif response.status == 409:
                ret['status'] = 'exists'
            else:
                ret['status'] = 'failed'

            return ret
        except Exception as e:
            logging.error(f'Error handling user: {e}')

        return ret

    @staticmethod
    async def add_referral(user_id: int, referral_id: int) -> bool:
        """
        Добавляет реферала пользователю.

        :param user_id: идентификатор пользователя
        :param referral_id: идентификатор реферала
        :return: True, если реферал был успешно добавлен, иначе False
        """
        try:
            await Backend.init_session()

            headers = {
                'x-admin-key': Settings.ADMIN_KEY
            }

            async with Backend.session.post('/api/v1/referrals/add_referral', json={'user_id': user_id, 'referral_id': referral_id}, headers=headers) as response:
                response.raise_for_status()

                if response.status == 200:
                    return True

            return False
        except Exception as e:
            logging.error(f'Error while adding referral: {e}')

            return False

    @staticmethod
    async def increase_balance_for_referrers() -> tuple:
        """
        Увеличивает баланс пользователей, которые имеют рефералов.

        :return: кортеж, содержащий статус операции и список пользователей,
                 у которых баланс был увеличен
        """
        try:
            await Backend.init_session()

            headers = {
                'x-admin-key': Settings.ADMIN_KEY
            }

            async with Backend.session.get('/api/v1/referrals/increase_balance_for_referrers', headers=headers) as response:
                response.raise_for_status()

                if response.status == 200:
                    data = await response.json()

                    if not data['users']:
                        return False, []

                    return True, data['users']

            return False, []
        except Exception as e:
            logging.error(f'Error while increasing balance for referrers: {e}')

    @staticmethod
    async def increase_balance_for_prefix(user_ids: list[int]) -> bool:
        """
        Увеличивает баланс пользователей, у которых есть тег "PSWMeta" в ни

        :param user_ids: список идентификаторов пользователей
        :return: True, если баланс был успешно увеличен, иначе False
        """
        try:
            await Backend.init_session()

            headers = {
                'x-admin-key': Settings.ADMIN_KEY
            }

            data = {
                'users': user_ids
            }

            async with Backend.session.post('/api/v1/referrals/increase_balance_for_prefix',
                                            json=data, headers=headers) as response:
                response.raise_for_status()

                if response.status == 200:
                    return True

            return False
        except Exception as e:
            logging.error(f'Error while updating balances for prefix: {e}')

            return False
