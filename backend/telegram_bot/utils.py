import re
from datetime import UTC, datetime, timedelta

from aiogram import types
from asgiref.sync import sync_to_async

from reminder.models.choices import ReminderTypeChoices
from reminder.models.models import Reminder
from reminder.utils import (
    parse_message_to_text,
    parse_text_to_reminder_data,
    save_reminder,
    GPT_MODELS,
    get_date_time_now,
    delete_reminders,
)
from telegram_bot.consts import (
    SYSTEM_MESSAGES,
    PRETTY_DATE_FORMAT,
    PRETTY_DATE_TIME_FORMAT,
    PRETTY_TIME_FORMAT,
    PRETTY_DATE_TIME_FORMAT_SHORT,
    PRETTY_DATE_FORMAT_SHORT,
    DEFAULT_TRANSLATION_LANGUAGE,
)
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


async def get_reminders(
    user_id: str, date_time: datetime | None = None
) -> list[Reminder]:
    if date_time:
        queryset = Reminder.objects.filter(
            date_time__date=date_time.date(), chat__user_id=user_id
        ).order_by("date_time")
    else:
        today = datetime.now(tz=UTC).date()
        queryset = Reminder.objects.filter(
            date_time__date__gte=today, chat__user_id=user_id
        ).order_by("date_time")
    reminders_list = await sync_to_async(list)(queryset)
    return reminders_list


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
            return "⏳"


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
        message_type=(
            MessageTypeChoices.TEXT if message.text else MessageTypeChoices.VOICE
        ),
    )
    text_message = await parse_message_to_text(message)
    await write_msg_to_db(
        chat_id=str(message.chat.id),
        message=text_message,
        message_from=MessageFromChoices.BOT,
        created_at=datetime.now(),
        message_type=MessageTypeChoices.TEXT,
    )

    reminders_to_create, reminders_to_delete = await parse_text_to_reminder_data(
        text_message, chat_instance
    )
    for reminder in [*reminders_to_create, *reminders_to_delete]:
        reminder |= {
            "chat": chat_instance,
        }
    #  --------------- To create ---------------
    message_to_user = ""
    saved_reminders = []  # to capture valid reminders
    for reminder in reminders_to_create:
        save_res = await save_reminder(reminder)
        if save_res is not None:
            saved_reminders.append(save_res)

    if saved_reminders:
        message_to_user += (
            "<b>We set these reminders for you:</b>\n"
            + "\n".join(
                [
                    f"{get_reminder_type_emoji(reminder.reminder_type)} {reminder.text}"
                    + f"({get_reminder_date_time(reminder.user_specified_date_time, chat_instance.get_utc_offset)}) "
                    + f"{get_reminder_delete_text(reminder.id)}"
                    for reminder in saved_reminders
                ]
            )
            + "\n\n"
        )
    #  --------------- To delete ---------------
    if reminders_to_delete:
        deleted_reminders = await delete_reminders(reminders_to_delete)
        message_to_user += "<b>We deleted these reminders for you:</b>\n" + "\n".join(
            [
                f"{get_reminder_type_emoji(reminder['reminder_type'])} {reminder['text']} ({get_reminder_date_time(reminder['user_specified_date_time'], chat_instance.get_utc_offset)})"
                for reminder in deleted_reminders
            ]
        )

    if not message_to_user:
        message_to_user = "I couldn't find any reminders to create or delete in your message. Please try again."
    return message_to_user


async def translate_message(text: str, language: str) -> str:
    if language == DEFAULT_TRANSLATION_LANGUAGE:
        return text

    text = await GPT_MODELS["gpt-4o-mini"].ainvoke(
        f"""
        Translate text to {language}. If text is already in {language}, don't translate it, just return it.
        Text to translate:
        {text}
    """
    )
    return text


async def get_help_message(message: types.Message) -> str:
    user_name = message.from_user.full_name
    chat_instance = await get_chat(message.chat.id)
    text = SYSTEM_MESSAGES["help_command"].format(
        user_name=(user_name if user_name else "there")
    )

    text = await translate_message(text, chat_instance.get_language)
    return text


def get_pretty_date_time_short(date: datetime) -> str:
    return date.strftime(PRETTY_DATE_TIME_FORMAT_SHORT)


def get_pretty_time(date: datetime) -> str:
    return date.strftime(PRETTY_TIME_FORMAT)


def get_reminder_date_time(date: datetime, offset_str: str = "+00:00") -> str:
    today = datetime.now(TgChat.get_timezone_by_str_offset(offset_str)).date()
    tomorrow = today + timedelta(days=1)

    formatted_time = get_pretty_time(date)
    if date.date() == today:
        return f"today at {formatted_time}"
    elif date.date() == tomorrow:
        return f"tomorrow at {formatted_time}"
    else:
        return f"{date.strftime(PRETTY_DATE_FORMAT_SHORT)} at {formatted_time}"


def _get_pretty_date_time(date: datetime) -> str:
    return date.strftime(PRETTY_DATE_TIME_FORMAT)


def _get_pretty_date(date: datetime) -> str:
    return date.strftime(PRETTY_DATE_FORMAT)


def get_pretty_date(only_date: bool = False, delta: int = 0) -> str:
    """
    Args:
        only_date: str - return only date
        delta: int - delta in minutes. If delta is not specified, return current date
    """
    return (
        _get_pretty_date(get_date_time_now() + timedelta(minutes=delta))
        if only_date
        else _get_pretty_date_time(get_date_time_now() + timedelta(minutes=delta))
    )


async def process_delete_reminder_command(message: types.Message) -> str:
    chat_instance = await get_chat(message.chat.id)
    match = re.search(r"(?<=rm_)\d+", message.text)
    if match:
        reminder_id_to_delete = match.group()
        reminder: Reminder = await sync_to_async(
            Reminder.objects.filter(id=reminder_id_to_delete, chat=chat_instance).first
        )()
        if not reminder:
            text = "This reminder was either deleted or you wrote wrong ID. Please try again."
        else:
            text = f"Reminder '{reminder.text}' on {get_reminder_date_time(reminder.user_specified_date_time, chat_instance.get_utc_offset)} was deleted."
            await sync_to_async(reminder.delete)()
    else:
        text = "We can't find any reminder to delete. Please try again."

    return await translate_message(text, chat_instance.get_language)


def get_reminder_delete_text(reminder_id: int) -> str:
    return f"(delete - /rm_{reminder_id})"
