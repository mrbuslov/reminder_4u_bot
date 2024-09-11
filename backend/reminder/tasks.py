# huey_daemon
from huey.contrib.djhuey import db_task
from asgiref.sync import sync_to_async


@db_task()
async def send_reminder(reminder_id: int) -> None:
    found_reminder = await sync_to_async(Reminder.objects.filter)(id=reminder_id)

    if not found_reminder:
        return

    raise NotImplementedError()
