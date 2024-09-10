from aiogram import Bot, Dispatcher

from core import settings

# Initialize bot and dispatcher
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
