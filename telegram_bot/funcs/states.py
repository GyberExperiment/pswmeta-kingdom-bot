from settings import privileged_user_states


def set_user_state(user_id, state, value=None):
    """
    Установить состояние пользователя.

    :param user_id: ID пользователя.
    :param state: Состояние пользователя.
    :param value: Значение состояния.
    """
    if user_id not in privileged_user_states:
        privileged_user_states[user_id] = {}

    privileged_user_states[user_id]['state'] = state

    if value is not None:
        privileged_user_states[user_id]['value'] = value


def get_user_state(user_id, include_value=False):
    """
    Получить состояние пользователя.

    :param user_id: ID пользователя.
    :param include_value: Включать ли значение состояния.
    :return: Состояние пользователя.
    """
    if user_id not in privileged_user_states:
        return None

    state = privileged_user_states[user_id]['state']

    if include_value:
        return state, privileged_user_states[user_id].get('value')

    return state


def clear_user_state(user_id):
    """
    Очистить состояние пользователя.

    :param user_id: ID пользователя.
    """
    if user_id in privileged_user_states:
        del privileged_user_states[user_id]
