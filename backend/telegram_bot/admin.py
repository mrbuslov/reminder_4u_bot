from django.contrib import admin
from telegram_bot.models import TgChat, TgMessage

admin.site.register(TgChat)
admin.site.register(TgMessage)
