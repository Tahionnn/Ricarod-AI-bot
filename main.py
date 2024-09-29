import asyncio
import random, string
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models.gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, CommandStart
from aiogram.filters.callback_data import CallbackData


class ChatsCbData(CallbackData, prefix="session_id"):
    id: str


api_token = '7731925488:AAGkJrATqkSNbBDfcZDXzTEusOrgLui6hGk'

model = GigaChat(
    credentials="NWY5Mjk0ZTktZGM1Ny00OTVhLWFhNmUtNjI4YTYyNWI2ZWU4OjlhNThkMmZjLWVjNjUtNDNjMS1hNzBjLTZiNmI2NjMzMmM4ZQ==",
    verify_ssl_certs=False,
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Ты Рикардо Милос. Бразильский танцор-бодибилдер. Ты каждое сообщение заканзчиваешь обращением \"ма бой\". Иногда отвечай на испанском.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)
chain = prompt | model

bot = Bot(token=api_token)
dp  = Dispatcher() 
store = {}
config = {"configurable": {"session_id": "abc15"}}
cb_data_first = ChatsCbData(id=config["configurable"]["session_id"])
config_id = {
    config["configurable"]["session_id"]: cb_data_first.pack(),
}


def create_inline_kb(width: int,
                     *args: str,
                     **kwargs: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    if args:
        for button in args:
            buttons.append(InlineKeyboardButton(
                text = button,
                callback_data=button))
    if kwargs:
        for button, text in kwargs.items():
            buttons.append(InlineKeyboardButton(
                text=button,
                callback_data=text))

    kb_builder.row(*buttons, width=width)

    return kb_builder.as_markup()


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer('Hello, my boy')


@dp.message(Command('help'))
async def start(message: types.Message):
    await message.answer('I\'m Ricardo. Just have fun with me, my boy')


@dp.message(Command('newchat'))
async def newchat(message: types.Message):
    global config
    global config_id

    letters = string.ascii_lowercase
    config["configurable"]["session_id"] = ''.join(random.choice(letters) for i in range(3))
    cb_data = ChatsCbData(id=config["configurable"]["session_id"])
    config_id[config["configurable"]["session_id"]] = cb_data.pack()

    await message.answer('--Начат Новый Чат--')


@dp.message(Command('chats'))
async def get_chats(message: types.Message):
    keyboard = create_inline_kb(len(config_id), **config_id)
    await message.answer("Ваши чаты с Рикардо", reply_markup=keyboard)


@dp.callback_query(ChatsCbData.filter())
async def switch_chat(
    callback_query: CallbackQuery,
    callback_data: ChatsCbData,
    ):
    config["configurable"]["session_id"] = callback_data.id
    await callback_query.answer(text=f"Вы сменили чат на {callback_data.id}", show_alert=True)


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


@dp.message()
async def send(message: types.Message):
    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="messages",
    )

    res = with_message_history.invoke(
        {
            "messages": [HumanMessage(content=message.text)]
        },
        config=config,
    )

    await message.answer(res.content)

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main()) 
