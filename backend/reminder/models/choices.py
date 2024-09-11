from django.db import models


class ReminderTypeChoices(models.TextChoices):
    MEETING = "meeting"
    OTHER = "other"
