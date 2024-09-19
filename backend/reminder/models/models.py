import datetime
from django.db import models

from reminder.models.choices import ReminderTypeChoices


class Reminder(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    date_time = models.DateTimeField(verbose_name="Date and time to remind")
    user_specified_date_time = models.DateTimeField(
        verbose_name="User specified date and time to remind in his timezone",
        default=datetime.datetime.now,
    )
    chat = models.ForeignKey("telegram_bot.TgChat", on_delete=models.CASCADE)
    reminder_type = models.CharField(
        max_length=50,
        choices=ReminderTypeChoices.choices,
        default=ReminderTypeChoices.OTHER,
    )
    task_id = models.CharField(
        max_length=36, null=True, verbose_name="Delayed task ID (UUID)"
    )

    @staticmethod
    def get_structure() -> dict:
        return {
            "text": "str",
            "date_time": "datetime",
            "user_specified_date_time": "datetime",
            "reminder_type": f"{ReminderTypeChoices.MEETING.value} | {ReminderTypeChoices.OTHER.value}",
        }
