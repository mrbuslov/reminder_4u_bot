# huey_daemon
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from core.settings import reminder_logger
from reminder.models.models import Reminder
from reminder.utils import get_date_time_now
from telegram_bot.decorators import get_running_loop
from telegram_bot.models.models import TgChat
from telegram_bot.settings import bot
from telegram_bot.utils import (
    get_reminders,
    translate_message,
    get_reminder_type_emoji,
    get_pretty_time,
    get_reminder_delete_text,
)


async def send_reminder_text(found_reminder: Reminder) -> bool:
    """Sends reminder to user."""

    try:
        reminder_text = await translate_message(
            found_reminder.reminder_text, found_reminder.chat.get_language
        )
        await bot.send_message(chat_id=found_reminder.chat.id, text=reminder_text)
        reminder_logger.error(f"Reminder was sent to {found_reminder.chat.id}")
        return True
    except TelegramForbiddenError:
        reminder_logger.info(
            f"Chat {found_reminder.chat.id} is not allowed to send messages"
        )
        return True
    except Exception as e:
        reminder_logger.error(f"Error while sending reminder: {e}")
        return False


async def send_reminders_for_today(reminders_list: list[Reminder]) -> None:
    """Sends reminder to user."""

    text = (
        """
    <b>Good morning! 👋 \nYour reminders for today:</b>
    """.strip()
        + "\n"
    )
    first_reminder = reminders_list[0]
    for reminder in reminders_list:
        text += (
            f"{get_reminder_type_emoji(reminder.reminder_type)}"
            + f"{get_pretty_time(reminder.user_specified_date_time)} - {reminder.reminder_text} "
            + f"{get_reminder_delete_text(reminder.id)}"
            + "\n"
        )

    try:
        reminder_text = await translate_message(text, first_reminder.chat.get_language)
        await bot.send_message(
            chat_id=first_reminder.chat.id,
            text=reminder_text,
            parse_mode=ParseMode.HTML,
        )
        reminder_logger.error(f"Reminder was sent to {first_reminder.chat.id}")
    except TelegramForbiddenError:
        reminder_logger.info(
            f"Chat {first_reminder.chat.id} is not allowed to send messages"
        )
    except Exception as e:
        reminder_logger.error(f"Error while sending reminder: {e}")


async def filter_n_send_reminders_for_today(chat_instance: TgChat) -> None:
    reminders_for_today = await get_reminders(
        chat_instance.user_id, date_time=get_date_time_now()
    )
    if reminders_for_today:
        await send_reminders_for_today(reminders_for_today)


# DEPRECATED: for some reason it doesn't work sometimes. So instead of scheduling it, we just write it to db
# and then with crontab we will send it
@db_task()
def send_reminder(reminder_id: int) -> None:
    """Sends reminder to user."""
    reminder_logger.info(f"Sending reminder {reminder_id}")
    found_reminder = (
        Reminder.objects.select_related("chat").filter(id=reminder_id).first()
    )
    if not found_reminder:
        reminder_logger.info(f"Reminder is not found {reminder_id}")
        return

    loop = get_running_loop()
    result = loop.run_until_complete(send_reminder_text(found_reminder))

    if result is not False:
        found_reminder.delete()


@db_periodic_task(crontab(minute="*/1"))
def check_reminder_every_num_mins():
    """
    Checks, if there are reminders that need to be sent.
    Sometimes reminders are missed - we do this for double check
    """

    reminder_logger.info(f"Checking reminders every 1 minute")
    expired_reminders = Reminder.objects.select_related("chat").filter(
        date_time__lte=get_date_time_now()
    )
    loop = get_running_loop()
    for reminder in expired_reminders:
        result = loop.run_until_complete(send_reminder_text(reminder))

        if result is not False:
            reminder.delete()


@db_periodic_task(crontab(minute="*/60"))
def send_reminders_for_today_in_the_morning():
    """Checks every hour for users in different timezones to send reminders for today at 8 am. by their time"""
    reminder_logger.info(f"Checking reminders 'for today' every 1 hour")
    chats_instances = list(TgChat.objects.all())
    chats_instances_with_morning_time = [
        chat_instance
        for chat_instance in chats_instances
        if chat_instance.get_datetime_in_user_timezone.hour == 8
    ]
    loop = get_running_loop()
    date_time = get_date_time_now()
    for chat_instance in chats_instances_with_morning_time:
        # TODO: make it work with filter_n_send_reminders_for_today func (can't do for now, strange error)
        reminders_list = list(
            Reminder.objects.select_related("chat")
            .filter(
                date_time__date=date_time.date(), chat__user_id=chat_instance.user_id
            )
            .order_by("date_time")
        )
        if reminders_list:
            loop.run_until_complete(send_reminders_for_today(reminders_list))
