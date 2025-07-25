# config.py
import os

from dotenv import load_dotenv
from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Другие секреты (пример)
    # TTS_API_KEY: SecretStr = Field(default=None)
    DB_PASSWORD: SecretStr = Field(default=None)


    # Настройки приложения
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()