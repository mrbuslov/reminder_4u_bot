import re

from django.db import models
from datetime import datetime, timedelta, timezone

from telegram_bot.consts import PATTERN_EXTRACT_UTC_FROM_LOCATION
from telegram_bot.models.choices import MessageFromChoices, MessageTypeChoices


class TgChat(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    region = models.CharField(
        max_length=100,
        verbose_name="Country or city user lives in + timezone",
        null=True,
    )
    language = models.CharField(max_length=100, null=True)

    name = models.CharField(max_length=50, null=True)
    username = models.CharField(max_length=50, null=True)
    user_id = models.CharField(max_length=50, null=True)

    @property
    def get_language(self) -> str:
        return self.language or "English"

    @property
    def get_region(self) -> str:
        return self.region or "Iceland (UTC+0)"

    @property
    def get_utc_offset(self) -> str:
        match = re.search(PATTERN_EXTRACT_UTC_FROM_LOCATION, self.get_region)
        return match.group() if match else "+00:00"

    @staticmethod
    def get_timezone_by_str_offset(offset_str: str) -> timezone:
        """If +00:00, return timezone obj"""
        # Extract hours and minutes from the offset string
        sign = 1 if offset_str[0] == "+" else -1
        hours, minutes = map(int, offset_str[1:].split(":"))

        utc_offset = timedelta(hours=sign * hours, minutes=sign * minutes)
        return timezone(utc_offset)

    @property
    def get_datetime_in_user_timezone(self) -> datetime:
        tz = self.get_timezone_by_str_offset(self.get_utc_offset)
        return datetime.now(tz)

    def __str__(self):
        return f"{self.id} - {self.name} {self.username} - {self.user_id} - ({self.get_region}, {self.get_language})"


class TgMessage(models.Model):
    tg_chat = models.ForeignKey(TgChat, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    message_from = models.CharField(max_length=50, choices=MessageFromChoices.choices)
    message_type = models.CharField(
        max_length=50,
        choices=MessageTypeChoices.choices,
        default=MessageTypeChoices.TEXT,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.message_from.capitalize()} - {self.tg_chat_id} ({self.message_type}): {self.message}"
