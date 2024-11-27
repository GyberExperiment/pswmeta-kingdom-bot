from dotenv import load_dotenv
from os import getenv
import os

import logging
from messages import current_welcome_message

from collections import defaultdict

from telebot.async_telebot import AsyncTeleBot

from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings


load_dotenv()
dir_path = "txtdata"


class Settings:
    APP_REFERRALS_URL = getenv('APP_REFERRALS_URL')
    TELEGRAM_BOT = getenv('TELEGRAM_BOT')
    COMMUNICATION_BASE_URL = getenv('COMMUNICATION_BASE_URL')
    ADMIN_KEY = getenv('ADMIN_KEY')
    API_KEY = getenv('API_KEY')
    DATABASE_DSN = getenv('DATABASE_DSN')
    CURRENT_WELCOME_MESSAGE = current_welcome_message




"""
Это вызывает проблемы, я пока отключил
"""
# PERSIST = True
# embeddings = OpenAIEmbeddings()
# if PERSIST and os.path.exists("ph/persist"):
#     logging.debug("Reusing index...\n")
#
#     vectorstore = Chroma(persist_directory="persist", embedding_function=embeddings)
#
#     index = VectorStoreIndexWrapper(vectorstore=vectorstore)
#
# else:
#     loader = DirectoryLoader(dir_path, show_progress=True)
#
#     if PERSIST:
#         index = VectorstoreIndexCreator(vectorstore_cls=Chroma,
#                                         embedding=embeddings,
#                                         vectorstore_kwargs={"persist_directory": "persist"}).from_loaders([loader])
#     else:
#         index = VectorstoreIndexCreator(embedding=embeddings).from_loaders([loader])
#
# chain = ConversationalRetrievalChain.from_llm(
#     llm=ChatOpenAI(model="gpt-4o"),
#     retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
# )

bot = AsyncTeleBot(Settings.TELEGRAM_BOT, parse_mode='HTML')

current_gif_file_id = "DEFAULT_FILE_ID"

privileged_users_id = {6846844984, 6227626197, 1821708942, 1055903122}

MAIN_CHAT_ID = int(os.getenv('MAIN_CHAT_ID'))

privileged_user_states = {}

chat_history = {}


user_referrals_requests = defaultdict(list)

MAX_REFERRALS_REQUESTS = 1
TIME_WINDOW_REFERRALS = 60

user_requests = defaultdict(list)

MAX_REQUESTS = 1
TIME_WINDOW = 1
