# huey_daemon
from datetime import timedelta

from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from core.settings import reminder_logger
from reminder.models.models import Reminder
from reminder.utils import get_date_time_now
from telegram_bot.decorators import get_running_loop
from telegram_bot.settings import bot


async def send_reminder_text(found_reminder: Reminder) -> None:
    """Sends reminder to user."""
    from telegram_bot.utils import translate_message

    reminder_text = await translate_message(
        found_reminder.text, found_reminder.chat.get_language
    )
    await bot.send_message(chat_id=found_reminder.chat.id, text=reminder_text)


@db_task()
def send_reminder(reminder_id: int) -> None:
    """Sends reminder to user."""
    reminder_logger.info(f"Sending reminder {reminder_id}")
    found_reminder = (
        Reminder.objects.select_related("chat").filter(id=reminder_id).first()
    )
    if not found_reminder:
        return

    loop = get_running_loop()
    loop.run_until_complete(send_reminder_text(found_reminder))

    found_reminder.delete()


should_skip_check_reminder = True


@db_periodic_task(crontab(minute="*/5"))
def check_reminder_every_five_mins():
    """
    Checks, if there are reminders that need to be sent.
    Sometimes reminders are missed - we do this for double check
    """
    reminder_logger.info(f"Checking reminders every 5 minutes")
    # when we start the bot, huey will automatically send reminders, so we don't need to check them 1st time
    global should_skip_check_reminder
    if should_skip_check_reminder:
        should_skip_check_reminder = False
        return

    # find reminders that have been expired more than 5 minutes
    expired_reminders = Reminder.objects.filter(
        date_time__lt=get_date_time_now() - timedelta(minutes=5)
    )
    for reminder in expired_reminders:
        reminder_logger.critical(
            f"Reminder is expired. Sending it with crontab func. Reminder text: '{reminder.text}'"
        )

        loop = get_running_loop()
        loop.run_until_complete(send_reminder_text(reminder))
        reminder.delete()
