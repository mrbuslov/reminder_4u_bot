from aiogram import types
from django.db import models

AVAILABLE_CONTENT_TYPES = [types.ContentType.TEXT, types.ContentType.VOICE]


class MessageFromChoices(models.TextChoices):
    USER = 'user'
    BOT = 'bot'


class MessageTypeChoices(models.TextChoices):
    TEXT = 'text'
    VOICE = 'voice'
