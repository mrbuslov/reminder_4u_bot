# huey_daemon
from datetime import timedelta

from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from core.settings import reminder_logger
from reminder.models.models import Reminder
from telegram_bot.decorators import get_running_loop
from telegram_bot.settings import bot
from aiogram.exceptions import TelegramForbiddenError


async def send_reminder_text(found_reminder: Reminder) -> bool:
    """Sends reminder to user."""
    from telegram_bot.utils import translate_message

    try:
        reminder_text = await translate_message(
            found_reminder.text, found_reminder.chat.get_language
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
    from reminder.utils import get_date_time_now

    reminder_logger.info(f"Checking reminders every 1 minute")
    expired_reminders = Reminder.objects.select_related("chat").filter(
        date_time__lte=get_date_time_now()
    )
    for reminder in expired_reminders:
        loop = get_running_loop()
        result = loop.run_until_complete(send_reminder_text(reminder))

        if result is not False:
            reminder.delete()
