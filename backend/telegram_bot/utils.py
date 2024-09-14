from datetime import datetime

from aiogram import types
from asgiref.sync import sync_to_async

from reminder.models.choices import ReminderTypeChoices
from reminder.utils import (
    parse_message_to_text,
    parse_text_to_reminder_data,
    save_reminder,
    GPT_MODELS,
)
from telegram_bot.consts import SYSTEM_MESSAGES
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


def get_reminder_type_emoji(reminder_type: ReminderTypeChoices) -> str:
    match reminder_type:
        case ReminderTypeChoices.MEETING:
            return "🗓"
        case ReminderTypeChoices.OTHER:
            return "✅"


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

    reminder_data_list = await parse_text_to_reminder_data(text_message, chat_instance)
    for reminder in reminder_data_list:
        reminder |= {
            "chat": chat_instance,
        }
        await save_reminder(reminder)

    if reminder_data_list:
        message_to_user = "<b>We set these reminders for you:</b>\n" + "\n".join(
            [
                f"{get_reminder_type_emoji(reminder['reminder_type'])} {reminder['text']}"
                for reminder in reminder_data_list
            ]
        )
        return message_to_user
    else:
        return "I didn't get that. Please try again."


async def translate_message(text: str, language: str) -> str:
    text = await GPT_MODELS["gpt-4o-mini"].ainvoke(
        f"""
        Translate this text to {language}:
        {text}
    """
    )
    return text


async def get_start_message(message: types.Message) -> str:
    user_name = message.from_user.full_name
    chat_instance = await get_chat(message.chat.id)
    text = SYSTEM_MESSAGES["start_command"].format(
        user_name=(user_name if user_name else "there")
    )
    if not chat_instance.region:
        text += "\n\nPlease set you <b>location</b> 📍 to get correctly your timezone. Use command /set_location"
    if not chat_instance.language:
        text += "\nAlso you can configure the <b>language</b> 🌍 of your reminders and how bot will talk to you. Use command /set_language"

    text = await translate_message(text, chat_instance.language)
    return text
