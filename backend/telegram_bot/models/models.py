from django.db import models

from telegram_bot.models.choices import MessageFromChoices, MessageTypeChoices


class TgChat(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    region = models.CharField(
        max_length=100, verbose_name="Country or city user lives in", null=True
    )
    language = models.CharField(max_length=100, null=True)

    name = models.CharField(max_length=50, null=True)
    username = models.CharField(max_length=50, null=True)
    user_id = models.CharField(max_length=50, null=True)

    def get_language(self):
        return self.language or "English"

    def get_region(self):
        return self.region or "Iceland (UTC+0)"

    def __str__(self):
        return f"{self.id} - {self.name} {self.username} - {self.user_id} - ({self.get_region()}, {self.get_language()})"


class TgMessage(models.Model):
    tg_chat = models.ForeignKey(TgChat, on_delete=models.CASCADE)
    message = models.TextField()
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
