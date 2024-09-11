from datetime import datetime

from aiogram import types
from asgiref.sync import sync_to_async

from reminder.utils import parse_message_to_text, parse_text_to_reminder_data
from telegram_bot.models.choices import MessageFromChoices, MessageTypeChoices
from telegram_bot.models.models import TgChat, TgMessage


@sync_to_async
def get_or_create_chat(chat_id: str) -> tuple[TgChat, bool]:
    return TgChat.objects.get_or_create(id=chat_id)


async def update_chat(chat_id: str, chat_data: dict) -> TgChat:
    chat, _ = await get_or_create_chat(chat_id)
    for key, value in chat_data.items():
        if value:
            setattr(chat, key, value)
    await sync_to_async(chat.save)()
    return chat


async def get_chat(chat_id) -> TgChat:
    chat, _ = await get_or_create_chat(chat_id)
    return chat


@sync_to_async
def get_chat_10_msgs(chat_id) -> list[TgMessage]:
    return list(TgMessage.objects.filter(tg_chat_id=chat_id))[:10]


async def write_msg_to_db(
    chat_id: str,
    message: str,
    message_from: str,
    created_at: datetime,
    message_type: MessageTypeChoices,
) -> None:
    chat = await get_chat(chat_id)
    await sync_to_async(TgMessage.objects.create)(
        tg_chat=chat,
        message=message,
        message_from=message_from,
        created_at=created_at,
        message_type=message_type,
    )


async def process_message(message: types.Message) -> str:
    chat_instance = await update_chat(
        chat_id=str(message.chat.id),
        chat_data={
            "name": message.chat.full_name,
            "username": message.chat.username,
            "user_id": message.from_user.id,
        },
    )
    await write_msg_to_db(
        chat_id=str(message.chat.id),
        message=message.text,
        message_from=MessageFromChoices.USER,
        created_at=message.date,
        message_type=MessageTypeChoices.TEXT
        if message.text
        else MessageTypeChoices.VOICE,
    )
    text_message = await parse_message_to_text(message)
    await write_msg_to_db(
        chat_id=str(message.chat.id),
        message=text_message,
        message_from=MessageFromChoices.BOT,
        created_at=datetime.now(),
        message_type=MessageTypeChoices.TEXT,
    )

    reminder_data = await parse_text_to_reminder_data(text_message, chat_instance)
    return text_message
