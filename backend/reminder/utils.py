import io
import json
import os
from datetime import datetime, timezone

import aiofiles
from aiogram import types
from langchain_core.prompts import PromptTemplate
from pydub import AudioSegment

from reminder.consts import (
    FILE_EXTENSION_TO_CONVERT_VOICE_AUDIO,
    REMINDER_EXTRACTION_PROMPT,
)
from reminder.models.models import Reminder
from reminder.schemas import GPTModel
from reminder.schemas import GPTModelName
from telegram_bot.models.models import TgChat
from telegram_bot.settings import bot
from dateutil.parser import parse

GPT_MODELS = {
    "gpt-4o": GPTModel(name=GPTModelName.GPT_4O, temperature=0.9),
    "gpt-4o-mini": GPTModel(name=GPTModelName.GPT_4O_MINI, temperature=0.9),
    "whisper-1": GPTModel(name=GPTModelName.WHISPER_1, temperature=0.9),
}


def is_json(json_str: str) -> bool:
    try:
        json.loads(json_str)
    except ValueError:
        return False
    return True


def get_date_time_now() -> datetime:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0)


async def save_voice_as_mp3(voice: types.Voice) -> str:
    """Downloads the voice message and saves it in mp3 format."""
    voice_file_info = await bot.get_file(voice.file_id)
    voice_ogg = io.BytesIO()
    await bot.download_file(voice_file_info.file_path, voice_ogg)

    directory = "temp_voice_files"
    if not os.path.exists(directory):
        os.makedirs(directory)

    voice_mp3_path = f"{directory}/voice-{voice.file_unique_id}.{FILE_EXTENSION_TO_CONVERT_VOICE_AUDIO}"
    AudioSegment.from_file(voice_ogg, format="ogg").export(
        voice_mp3_path, format=FILE_EXTENSION_TO_CONVERT_VOICE_AUDIO
    )
    return voice_mp3_path


async def parse_message_to_text(message: types.Message) -> str:
    """It takes either text or voice message and converts to text"""
    if message.text:
        return message.text
    elif message.voice:
        voice_mp3_path = await save_voice_as_mp3(message.voice)
        try:
            async with aiofiles.open(voice_mp3_path, "rb") as f:
                file_content = await f.read()
                buffer = io.BytesIO(file_content)
                text = await GPT_MODELS[GPTModelName.GPT_4O.value].ainvoke_audio(buffer)
            return text
        except Exception as e:
            # TODO: add logging
            print(e)
            return ""
        finally:
            os.remove(voice_mp3_path)


async def parse_text_to_reminder_data(text: str, chat: TgChat) -> list[dict]:
    model = GPT_MODELS[GPTModelName.GPT_4O.value]
    prompt = PromptTemplate.from_template(REMINDER_EXTRACTION_PROMPT)
    chain = prompt | model.llm_instance
    res = await chain.ainvoke(
        {
            "user_message": text,
            "location": chat.get_region(),
            "reminder_structure": Reminder.get_structure(),
            "time_now": str(get_date_time_now()),
        }
    )
    reminders_data_list_output = res.content
    print("reminders_data_list_output", reminders_data_list_output)
    reminders_data_list = (
        json.loads(reminders_data_list_output)
        if is_json(reminders_data_list_output)
        else []
    )
    # turn datetime string to datetime object
    for reminder_data in reminders_data_list:
        reminder_data["date_time"] = parse(reminder_data["date_time"])
    print("reminders_data_list", reminders_data_list)
    return reminders_data_list


async def save_reminder(reminder_data: dict) -> bool:
    # do_something.schedule((instance,), delay=3600)
    pass


async def delete_reminder(reminder_tak_id: str) -> bool:
    # https://github.com/coleifer/huey/issues/178
    pass
