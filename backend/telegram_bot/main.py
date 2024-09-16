import asyncio

from aiogram import F, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from core.settings import logger
from reminder.utils import GPT_MODELS, get_date_time_now
from telegram_bot.consts import AVAILABLE_CONTENT_TYPES, SYSTEM_MESSAGES
from telegram_bot.settings import dp, bot
from telegram_bot.utils import (
    process_message,
    update_chat,
    get_chat,
    get_start_message,
    translate_message,
    get_pretty_date,
    get_help_message,
    get_reminders,
    get_reminder_type_emoji,
    _get_pretty_time,
    _get_pretty_date,
    _get_pretty_date_time,
    _get_pretty_date_time_short,
)


class HelpStates(StatesGroup):
    waiting_for_setting_location = State()
    waiting_for_setting_language = State()


# ---------------------- Commands processing ----------------------
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    text = await get_start_message(message)
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(Command("help"))
async def help_command(message: types.Message):
    text = await get_help_message(message)
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(StateFilter(None), Command("set_location"))
async def set_location_command(message: types.Message, state: FSMContext):
    await state.set_state(HelpStates.waiting_for_setting_location)
    chat_instance = await get_chat(message.chat.id)
    text = await translate_message(
        SYSTEM_MESSAGES["location_command"], chat_instance.language
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(HelpStates.waiting_for_setting_location)
async def set_location_command_waiting_for_value(
    message: types.Message, state: FSMContext
):
    chat_instance = await get_chat(message.chat.id)
    region_n_timezone = await GPT_MODELS["gpt-4o-mini"].ainvoke(
        f"""
        User sent the message with location.
        Your task is to get location and timezone from the location in this format: <location> <UTC+00:00>
        You MUST write IN ENGLISH!
        If you can't get timezone, return None
        You MUST return location + timezone or None, don't write anything else!
        Today is {get_pretty_date(only_date=True)}
        User message: {message.text}
    """
    )
    if region_n_timezone == "None":
        text = await translate_message(
            SYSTEM_MESSAGES["location_not_changed"], chat_instance.language
        )
        await message.answer(text, parse_mode=ParseMode.HTML)
    else:
        await update_chat(
            chat_id=str(message.chat.id),
            chat_data={
                "region": region_n_timezone,
            },
        )
        text = await translate_message(
            SYSTEM_MESSAGES["location_changed"].format(
                region_n_timezone=region_n_timezone
            ),
            chat_instance.language,
        )
        await message.answer(text, parse_mode=ParseMode.HTML)
    await state.clear()


@dp.message(StateFilter(None), Command("set_language"))
async def set_language_command(message: types.Message, state: FSMContext):
    await state.set_state(HelpStates.waiting_for_setting_language)
    chat_instance = await get_chat(message.chat.id)
    text = await translate_message(
        SYSTEM_MESSAGES["language_command"], chat_instance.language
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(HelpStates.waiting_for_setting_language)
async def set_language_command_waiting_for_value(
    message: types.Message, state: FSMContext
):
    chat_instance = await get_chat(message.chat.id)
    language = await GPT_MODELS["gpt-4o-mini"].ainvoke(
        f"""
        User sent the message with the preferred language he wants to speak in.
        Your task is to extract language in this format: Russian
        You MUST write language IN ENGLISH!
        You MUST extract ONLY one language.
        If you can't identify language, return None
        You MUST return language or None, don't write anything else!
        User message: {message.text}
    """
    )
    if language == "None":
        text = await translate_message(
            SYSTEM_MESSAGES["language_not_changed"], chat_instance.language
        )
        await message.answer(text, parse_mode=ParseMode.HTML)
    else:
        await update_chat(
            chat_id=str(message.chat.id),
            chat_data={
                "language": language,
            },
        )
        text = await translate_message(
            SYSTEM_MESSAGES["language_changed"].format(language=language),
            chat_instance.language,
        )
        await message.answer(text, parse_mode=ParseMode.HTML)
    await state.clear()


@dp.message(Command("list"))
async def list_command(message: types.Message):
    chat_instance = await get_chat(message.chat.id)
    reminders_for_today = await get_reminders(
        chat_instance.user_id, date_time=get_date_time_now()
    )
    if reminders_for_today:
        text = """
        <b>Your reminders for today:</b>
        """
        for reminder in reminders_for_today:
            text += (
                f"""
            {get_reminder_type_emoji(reminder.reminder_type)} {_get_pretty_time(reminder.user_specified_date_time)} - {reminder.text}
            """.strip()
                + "\n"
            )
    else:
        text = SYSTEM_MESSAGES["list_command_invalid"]
    text = await translate_message(text, chat_instance.language)
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(Command("list_all"))
async def list_all_command(message: types.Message):
    chat_instance = await get_chat(message.chat.id)
    all_reminders = await get_reminders(chat_instance.user_id)
    if all_reminders:
        text = """
        <b>Your all reminders:</b>
        """
        for reminder in all_reminders:
            text += (
                f"""
            {get_reminder_type_emoji(reminder.reminder_type)} {_get_pretty_date_time_short(reminder.user_specified_date_time)} - {reminder.text}
            """.strip()
                + "\n"
            )
    else:
        text = SYSTEM_MESSAGES["list_all_command_invalid"]
    text = await translate_message(text, chat_instance.language)
    await message.answer(text, parse_mode=ParseMode.HTML)


# ---------------------- Messages processing ----------------------
@dp.message(F.content_type == types.ContentType.VOICE)
async def process_voice_message(message: types.Message):
    chat_instance = await get_chat(message.chat.id)
    text = await translate_message(
        SYSTEM_MESSAGES["message_voice_processing"], chat_instance.language
    )
    first_message = await message.answer(text, parse_mode=ParseMode.HTML)
    result = await process_message(message)
    result = await translate_message(result, chat_instance.language)
    await bot.delete_message(
        chat_id=first_message.chat.id, message_id=first_message.message_id
    )
    await message.answer(result, parse_mode=ParseMode.HTML)


@dp.message(F.content_type == types.ContentType.TEXT)
async def process_text_message(message: types.Message):
    chat_instance = await get_chat(message.chat.id)
    text = await translate_message(
        SYSTEM_MESSAGES["message_text_processing"], chat_instance.language
    )
    first_message = await message.answer(text, parse_mode=ParseMode.HTML)
    result = await process_message(message)
    result = await translate_message(result, chat_instance.language)
    await bot.delete_message(
        chat_id=first_message.chat.id, message_id=first_message.message_id
    )
    await message.answer(result, parse_mode=ParseMode.HTML)


@dp.message(lambda message: message.content_type not in AVAILABLE_CONTENT_TYPES)
async def process_any_other_message(message: types.Message):
    chat_instance = await get_chat(message.chat.id)
    text = await translate_message(
        SYSTEM_MESSAGES["message_any"], chat_instance.language
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Starting Telegram Bot...")
    asyncio.run(main())
