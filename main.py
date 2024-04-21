import json
from bot.utils import (
    ask_llm,
    get_prompt,
    translate_sentence
)
from bot.consts import prompt, DEFAULT_TIME_ZONE_LOCATION
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from bot.settings import settings
from dateutil import parser as date_parser


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
    with open('db.json', 'r') as f:
        db_json: dict = json.loads(f.read())

    prompt = get_prompt(
        message.text,
        db_json.get(message.from_user.id) or DEFAULT_TIME_ZONE_LOCATION
    )
    res = await ask_llm(prompt)
    res = json.loads(res)
    print('res', res)
    
    resp_text = ''
    if not res.get('reminder_text') or not res.get('time'):
        resp_text = "Sorry, AI couldn't identify reminder text of time. Please, try again"
    else:
        time = date_parser.parse(res['time']).strftime("%H:%M, %b %d")
        resp_text = f"Reminder text: {res['reminder_text']}\nTime: {time}"
    
    await message.answer(resp_text)



async def main() -> None:
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Starting...')
    asyncio.run(main())
