from datetime import datetime

from aiogram import types
from asgiref.sync import sync_to_async

from reminder.utils import parse_message_to_text
from telegram_bot.models import TgChat, TgMessage


async def get_chat(chat_id):
    chat, _ = await sync_to_async(TgChat.objects.get_or_create)(id=chat_id)
    return chat


@sync_to_async
def get_chat_10_msgs(chat_id) -> list[TgMessage]:
    return list(TgMessage.objects.filter(tg_chat_id=chat_id))[-9:]


async def write_msg_to_db(
        name: str,
        username: str,
        chat_id: str,
        message: str,
        user_id: int,
        date: datetime
):
    chat = await get_chat(chat_id)
    await sync_to_async(TgMessage.objects.create)(
        tg_chat=chat,
        name=name,
        username=username,
        message=message,
        user_id=user_id,
        date=date,
    )


async def process_message(message: types.Message) -> str:
    text_message = await parse_message_to_text(message)
    return text_message
