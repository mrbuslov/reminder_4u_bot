import io
import json
import os
from datetime import datetime, timezone

import aiofiles
from aiogram import types
from langchain_core.prompts import PromptTemplate
from pydub import AudioSegment

from core.settings import logger
from manage import huey_instance
from reminder.consts import (
    FILE_EXTENSION_TO_CONVERT_VOICE_AUDIO,
    REMINDER_TO_DELETE_EXTRACTION_PROMPT,
    REMINDER_EXTRACTION_PROMPT_DETAILED,
    REMINDER_EXTRACTION_PROMPT_JSON,
)
from reminder.models.models import Reminder
from reminder.schemas import GPTModel
from reminder.schemas import GPTModelName
from telegram_bot.models.models import TgChat
from telegram_bot.settings import bot
from dateutil.parser import parse
from asgiref.sync import sync_to_async
from reminder.tasks import send_reminder
from django.db import transaction

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
            logger.critical(f"Error in parse_message_to_text: {e}")
            return ""
        finally:
            os.remove(voice_mp3_path)


async def parse_text_to_reminder_data(
    text: str, chat: TgChat
) -> tuple[list[dict], list[dict]]:
    logger.info(f"Creating reminder, user_message: {text}")
    model = GPT_MODELS[GPTModelName.GPT_4O.value]
    # for better response quality we should make 2 requests
    # --- 1st request ---
    prompt = PromptTemplate.from_template(REMINDER_EXTRACTION_PROMPT_DETAILED)
    chain = prompt | model.llm_instance
    res = await chain.ainvoke(
        {
            "user_message": text,
            "reminder_structure": Reminder.get_structure(),
            "time_now": str(get_date_time_now()),
            "user_time_now": str(chat.get_datetime_in_user_timezone),
        }
    )
    reminders_data_unstructured_output = res.content
    logger.info(
        f"reminders_data_unstructured_output: {reminders_data_unstructured_output}"
    )
    # --- 2nd request ---
    prompt = PromptTemplate.from_template(REMINDER_EXTRACTION_PROMPT_JSON)
    chain = prompt | model.llm_instance
    res = await chain.ainvoke(
        {
            "reminders_in_txt": reminders_data_unstructured_output,
            "reminder_structure": Reminder.get_structure(),
            "time_now": str(get_date_time_now()),
            "user_time_now": str(chat.get_datetime_in_user_timezone),
            "response_structure": """{
                "to_create": "list[<reminder_structure>]",
                "to_delete": "list[<reminder_structure>]",
            }""",
        }
    )
    reminders_data_dict_output = res.content.replace("```json", "").replace("```", "")

    logger.info(f"reminders_data_dict_output: {reminders_data_dict_output}")
    reminders_data_dict = (
        json.loads(reminders_data_dict_output)
        if is_json(reminders_data_dict_output)
        else {}
    )
    to_create, to_delete = reminders_data_dict.get(
        "to_create", []
    ), reminders_data_dict.get("to_delete", [])
    # turn datetime string to datetime object
    for reminder_data in [*to_create, *to_delete]:
        reminder_data["date_time"] = parse(reminder_data["date_time"])
        reminder_data["user_specified_date_time"] = parse(
            reminder_data["user_specified_date_time"].split("+")[
                0
            ]  # rm timezone, bc time is already in user timezone
        )
    logger.info(f"to_create: {to_create}")
    logger.info(f"to_delete: {to_delete}")
    return to_create, to_delete


async def save_reminder(reminder_data: dict) -> Reminder | None:
    if reminder_data["date_time"] < get_date_time_now():
        return None

    reminder_obj = await sync_to_async(Reminder.objects.create)(**reminder_data)
    task = send_reminder.schedule((reminder_obj.id,), eta=reminder_obj.date_time)
    reminder_obj.task_id = task.id
    await sync_to_async(reminder_obj.save)()
    return reminder_obj


def _delete_reminder_from_db_n_task(reminder: Reminder) -> bool:
    with transaction.atomic():
        try:
            reminder_task_id = reminder.task_id
            reminder.delete()
            # place it after deleting reminder
            if reminder_task_id:
                huey_instance.revoke_by_id(reminder_task_id)
            return True
        except Exception as e:
            logger.info(f"Failed to delete reminder: {e}")
            return False


async def delete_reminders(reminders_datas_list: list[dict]) -> list[dict]:
    if not reminders_datas_list:
        return []

    deleted_reminders = []
    model = GPT_MODELS[GPTModelName.GPT_4O.value]
    prompt = PromptTemplate.from_template(REMINDER_TO_DELETE_EXTRACTION_PROMPT)
    chain = prompt | model.llm_instance

    all_reminders_filtered = await sync_to_async(Reminder.objects.filter)(
        chat__user_id=reminders_datas_list[0]["chat"].user_id
    )
    all_reminders_list = await sync_to_async(list)(all_reminders_filtered)
    all_reminders_list_str = [
        f"""
        id: {reminder.id}
        reminder text: {reminder.text}
        date and time for reminder execution: {reminder.user_specified_date_time}
        reminder type: {reminder.reminder_type}
        """
        + "\n"
        for reminder in all_reminders_list
    ]
    res = await chain.ainvoke(
        {
            "user_provided_reminders": reminders_datas_list,
            "all_reminders_list": all_reminders_list_str,
        }
    )
    reminders_to_delete_output = res.content
    reminders_ids_to_delete = (
        json.loads(reminders_to_delete_output)
        if is_json(reminders_to_delete_output)
        else []
    )
    logger.info(f"reminders_ids_to_delete: {reminders_ids_to_delete}")
    for reminder_id_to_delete in reminders_ids_to_delete:
        reminder = await sync_to_async(Reminder.objects.get)(id=reminder_id_to_delete)
        reminder_data = {
            "reminder_type": reminder.reminder_type,
            "text": reminder.text,
        }
        res = await sync_to_async(_delete_reminder_from_db_n_task)(reminder)
        if res is True:
            # put it to the end, so transaction will be rolled back if any one of them fails
            deleted_reminders.append(reminder_data)

    return deleted_reminders
