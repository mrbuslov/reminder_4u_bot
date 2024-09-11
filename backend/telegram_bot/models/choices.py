from django.db import models


class MessageFromChoices(models.TextChoices):
    USER = "user"
    BOT = "bot"


class MessageTypeChoices(models.TextChoices):
    TEXT = "text"
    VOICE = "voice"
