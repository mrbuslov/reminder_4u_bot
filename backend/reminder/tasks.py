# huey_daemon
from huey.contrib.djhuey import db_task

from reminder.models.models import Reminder
from telegram_bot.decorators import get_running_loop
from telegram_bot.settings import bot


async def send_reminder_text(found_reminder: Reminder) -> None:
    """Sends reminder to user."""
    from telegram_bot.utils import translate_message

    reminder_text = await translate_message(
        found_reminder.text, found_reminder.chat.get_language()
    )
    await bot.send_message(chat_id=found_reminder.chat.id, text=reminder_text)


@db_task()
def send_reminder(reminder_id: int) -> None:
    """Sends reminder to user."""
    found_reminder = (
        Reminder.objects.select_related("chat").filter(id=reminder_id).first()
    )
    if not found_reminder:
        return

    loop = get_running_loop()
    loop.run_until_complete(send_reminder_text(found_reminder))

    found_reminder.delete()
