from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: SecretStr = Field(..., min_length=32)

    # Другие секреты (пример)
    # TTS_API_KEY: SecretStr = Field(default=None)
    # DB_PASSWORD: SecretStr = Field(default=None)

    # Настройки приложения
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Создаем экземпляр настроек


config = Settings()