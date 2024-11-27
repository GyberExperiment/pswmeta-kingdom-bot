def get_langchain_response(query, chat_history):
    """
    Получить ответ от AI.

    :param query: Запрос пользователя.
    :param chat_history: История переписки.
    :return: Ответ от AI.
    """
    # Длинное сообщение с промптом для AI
    result = chain.invoke({"question": "Respond like an expert with confidence, providing well-structured, detailed, and accurate answers. Even when unfamiliar with a topic, use related knowledge, research skills, or logical reasoning to construct reliable responses. Ensure your answers are clear, concise, comprehensive, and engaging, using a balanced perspective to convey depth and critical thinking. Anticipate follow-up questions, include practical examples or analogies, and maintain a personable tone to make complex ideas accessible and relatable. use html telegram format: " + query, "chat_history": chat_history})    # noqa

    return result['answer']
