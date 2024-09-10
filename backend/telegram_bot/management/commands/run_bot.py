import asyncio

from django.core.management.base import BaseCommand

from telegram_bot.main import main


class Command(BaseCommand):
    help = '-'

    def handle(self, *args, **kwargs):
        asyncio.run(main())
