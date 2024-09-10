import io
import os

from aiogram import types
from pydub import AudioSegment

from reminder.consts import FILE_EXTENSION_TO_CONVERT_VOICE_AUDIO
from reminder.schemas import GPTModelName, GPTModel
from telegram_bot.settings import bot
import aiofiles

GPT_MODELS = {
    "gpt-4o": GPTModel(name=GPTModelName.GPT_4O, temperature=0.9),
    "gpt-4o-mini": GPTModel(name=GPTModelName.GPT_4O_MINI, temperature=0.9),
    "whisper-1": GPTModel(name=GPTModelName.WHISPER_1, temperature=0.9),
}


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
            async with aiofiles.open(voice_mp3_path, 'rb') as f:
                file_content = await f.read()
                buffer = io.BytesIO(file_content)
                text = await GPT_MODELS[GPTModelName.GPT_4O.value].ainvoke_audio(buffer)
            return text
        except Exception as e:
            # TODO: add logging
            print(e)
            return ''
        finally:
            os.remove(voice_mp3_path)

