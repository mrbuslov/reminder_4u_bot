from bot.utils import (
    prompt,
    ask_llm,
    translate_sentence
)
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from bot.settings import settings


# Initialize bot and dispatcher
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    user_name = message.from_user.full_name
    text = (
        f"Hello {user_name if user_name else 'there'} 👋! I'm the AI Reminder bot. 🤖\n"
        "You send me your free-form text reminders, and I'll make sure you never forget them!\n"
        "Just drop your reminders here, and I'll handle the rest. Give it a try!"
    )
    
    await message.reply(text)

    
@dp.message()
async def any_message(message: types.Message):
    prompt_formatted = prompt + message.text
    res = await ask_llm(prompt_formatted)
    
    await message.answer(res)



async def main() -> None:
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Starting...')
    asyncio.run(main())
