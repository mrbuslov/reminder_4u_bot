from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    DEEPL_TOKEN: Optional[str] = None # NOTE: if not provided, we'll use free version - googletrans
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
