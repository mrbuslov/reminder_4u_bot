import asyncio

from aiogram import F, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart

from telegram_bot.consts import AVAILABLE_CONTENT_TYPES
from telegram_bot.settings import dp, bot
from telegram_bot.utils import process_message


@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    user_name = message.from_user.full_name
    text = (
        f"Hello {user_name if user_name else 'there'} 👋! I'm the AI Reminder bot. 🤖\n"
        "You send me your free-form text OR voice reminders, and I'll make sure you never forget them!\n"
        "Just drop your reminders here, and I'll handle the rest. Give it a try!"
    )

    await message.reply(text)


@dp.message(F.content_type == types.ContentType.VOICE)
async def process_voice_message(message: types.Message):
    first_message = await message.answer('Voice message received. Processing the reminder...')
    result = await process_message(message)
    await bot.delete_message(
        chat_id=first_message.chat.id,
        message_id=first_message.message_id
    )
    await message.answer(result)


@dp.message(F.content_type == types.ContentType.TEXT)
async def process_text_message(message: types.Message):
    first_message = await message.answer('Text message received. Processing the reminder...')
    result = await process_message(message)
    await bot.delete_message(
        chat_id=first_message.chat.id,
        message_id=first_message.message_id
    )
    await message.answer(result)


@dp.message(lambda message: message.content_type not in AVAILABLE_CONTENT_TYPES)
async def process_any_other_message(message: types.Message):
    await message.answer(
        "Sorry, we don't accept such type of messages. Please, send a <u>voice</u> or <u>text</u> message",
        parse_mode=ParseMode.HTML
    )


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Starting...')
    asyncio.run(main())
