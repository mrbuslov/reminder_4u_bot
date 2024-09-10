from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables.base import RunnableSerializable
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from strenum import StrEnum

from core import settings
from reminder.consts import FILE_EXTENSION_TO_CONVERT_VOICE_AUDIO


class GPTModelName(StrEnum):
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    WHISPER_1 = "whisper-1"


@dataclass
class GPTModel:
    name: GPTModelName
    temperature: float

    def __post_init__(self) -> None:
        self.__llm_instance = ChatOpenAI(model=self.name, temperature=self.temperature, api_key=settings.OPENAI_API_KEY)
        self.__async_openai_instance = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @property
    def llm_instance(self) -> ChatOpenAI:
        return self.__llm_instance

    async def ainvoke(self, text: str, runnable: RunnableSerializable | None = None) -> str | None:
        this_runnable = self.llm_instance
        if runnable is not None:
            this_runnable = runnable
        try:
            res = await this_runnable.ainvoke(text).content
        except Exception as e:
            print(e)
            res = None
        return res

    async def ainvoke_audio(self, audio: BytesIO) -> str | None:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        result = None
        try:
            # In order for the Whisper API to work, the buffer with the audio-bytes has to have a name
            audio.name = 'file.' + FILE_EXTENSION_TO_CONVERT_VOICE_AUDIO
            transcription = await client.audio.transcriptions.create(
                model="whisper-1", file=audio
            )
            result = transcription.text
        except Exception as e:
            # TODO: logging
            print(
                f"Open API error: {e}"
            )
        return result


class ReminderType(StrEnum):
    OTHER = "other"
    MEETING = "meeting"


class ReminderSchema(BaseModel):
    date: datetime = Field(description="The date and time to set a reminder")
    type: ReminderType = Field(description=f"The type of the reminder. Default: {ReminderType.OTHER}")
    text: str = Field(description="The text of the reminder")


class RemindersListSchema(BaseModel):
    reminders: list[ReminderSchema] = Field(description="The list of reminders")
