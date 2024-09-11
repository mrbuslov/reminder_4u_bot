from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "telegram_bot"

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from telegram_bot.models.models import TgChat, TgMessage
        from . import main
