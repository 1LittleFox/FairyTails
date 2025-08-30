# app/config.py
import json
import logging
from functools import lru_cache
from typing import Dict, Any, Optional, List
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Центральная конфигурация приложения для Pydantic V2.
    Все секретные данные загружаются из переменных окружения.
    """

    # === ОСНОВНЫЕ НАСТРОЙКИ ===
    debug: bool = False
    uvicorn_reload: bool = False
    environment: str = "production"

    # === OPENAI НАСТРОЙКИ ===
    openai_api_key: str
    openai_model: str = "gpt-5"
    openai_model_for_markup: str = "gpt-4o"

    # Таймауты для OpenAI (в секундах)
    openai_timeout_connect: float = 30.0
    openai_timeout_read: float = 900.0

    # === БАЗА ДАННЫХ ===
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 30

    # === SELECTEL S3 ===
    selectel_access_key: str
    selectel_secret_key: str
    selectel_bucket_name: str
    selectel_domain: str

    # === GOOGLE CLOUD ===
    google_cloud_project_id: Optional[str] = None
    temp_gcs_bucket_name: Optional[str] = None
    google_cloud_credentials: Optional[str] = None

    # === YANDEX CLOUD ===
    yandex_api_key: str
    yandex_folder_id: str

    # === БЕЗОПАСНОСТЬ ===
    allowed_origins: List[str] = [
        "http://127.0.0.1:8000"
    ]

    # === НАСТРОЙКИ СЕРВЕРА ===
    server_ip: Optional[str] = None
    server_domain: Optional[str] = None  # Когда получите домен

    # === ЛИМИТЫ И ПРОИЗВОДИТЕЛЬНОСТЬ ===
    max_request_size_mb: int = 10
    rate_limit_requests_per_minute: int = 3
    story_generation_timeout: int = 600  # 10 минут

    # === ЛОГИРОВАНИЕ ===
    log_level: str = "INFO"
    log_format: str = "json"

    # === МОНИТОРИНГ ===
    sentry_dsn: Optional[str] = None
    metrics_enabled: bool = True

    # Конфигурация для Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False,
        # Автоматическое сопоставление имен переменных
        # debug -> DEBUG, openai_api_key -> OPENAI_API_KEY
        env_prefix="",
        extra="ignore"  # Игнорировать лишние переменные окружения
    )

    # === ВАЛИДАТОРЫ (Pydantic V2 синтаксис) ===

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not v or not v.startswith("sk-"):
            raise ValueError("OpenAI API key должен начинаться с 'sk-'")
        if len(v) < 20:
            raise ValueError("OpenAI API key слишком короткий")
        return v

    @field_validator("openai_model")
    @classmethod
    def validate_openai_model(cls, v: str) -> str:
        allowed_models = [
            "gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo",
            "gpt-4", "gpt-3.5-turbo"
        ]
        if v not in allowed_models:
            raise ValueError(f"Модель {v} не поддерживается. Доступны: {allowed_models}")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL должен начинаться с postgresql:// или postgresql+asyncpg://")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"LOG_LEVEL должен быть одним из: {allowed_levels}")
        return v.upper()

    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"ENVIRONMENT должен быть одним из: {allowed_envs}")
        return v

    @field_validator("allowed_origins", mode='before')
    @classmethod
    def validate_origins(cls, v):
        if isinstance(v, str):
            # Если передана строка, разделяем по запятым
            return [origin.strip() for origin in v.split(",")]
        return v

    @model_validator(mode='after')
    def validate_google_cloud_settings(self) -> 'Settings':
        """Проверяем, что Google Cloud настройки согласованы"""
        if self.google_cloud_project_id and not self.google_cloud_credentials:
            raise ValueError("Если указан GOOGLE_CLOUD_PROJECT_ID, необходимо указать GOOGLE_CLOUD_CREDENTIALS")
        return self

    # === ПРОИЗВОДНЫЕ СВОЙСТВА ===

    @property
    def is_development(self) -> bool:
        """Проверка, что мы в режиме разработки"""
        return self.environment == "development" or self.debug

    @property
    def is_production(self) -> bool:
        """Проверка, что мы в продакшене"""
        return self.environment == "production"

    @property
    def google_cloud_credentials_dict(self) -> Optional[Dict[str, Any]]:
        """Возвращает Google Cloud credentials как словарь"""
        if not self.google_cloud_credentials:
            return None
        try:
            return json.loads(self.google_cloud_credentials)
        except json.JSONDecodeError as e:
            raise ValueError(f"Неверный формат GOOGLE_CLOUD_CREDENTIALS: {e}")

    @property
    def max_request_size_bytes(self) -> int:
        """Максимальный размер запроса в байтах"""
        return self.max_request_size_mb * 1024 * 1024

    @property
    def openai_timeout_config(self) -> dict:
        """Конфигурация таймаутов для OpenAI"""
        return {
            "connect": self.openai_timeout_connect,
            "read": self.openai_timeout_read,
            "write": 30.0,
            "pool": 30.0
        }

    def get_server_urls(self) -> List[str]:
        """Генерирует список серверных URL"""
        urls = []

        if self.server_domain:
            urls.extend([
                f"https://{self.server_domain}",
                f"https://www.{self.server_domain}",
            ])

        if self.server_ip:
            urls.extend([
                f"https://{self.server_ip}",
                f"http://{self.server_ip}:8000",  # На случай, если SSL еще не настроен
            ])

        return urls

    def get_cors_config(self) -> dict:
        """Возвращает безопасную конфигурацию CORS"""

        if self.is_development:
            # Для разработки - разрешаем локальные адреса
            allowed_origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8080",
            ]
        else:
            # Для продакшена - начинаем с серверных URL
            allowed_origins = self.get_server_urls()

            # Добавляем дополнительные origins из .env
            # allowed_origins.extend(self.additional_origins)

            # Убираем дубликаты
        allowed_origins = list(set(filter(None, allowed_origins)))

        return {
            "allow_origins": allowed_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "Accept",
                "Accept-Language",
                "X-Request-ID"
            ],
            "expose_headers": ["X-Request-ID"],
            "max_age": 3600 if not self.is_development else 600
        }

    def log_server_info(self) -> None:
        """Выводит информацию о сервере"""
        logger = logging.getLogger(__name__)

        logger.info("🌐 Server Configuration:")
        if self.server_domain:
            logger.info(f"  📍 Domain: {self.server_domain}")
        if self.server_ip:
            logger.info(f"  📍 IP: {self.server_ip}")

        server_urls = self.get_server_urls()
        if server_urls:
            logger.info(f"  🔗 Available URLs: {server_urls}")
        else:
            logger.warning("  ⚠️  No server URLs configured! Set SERVER_IP or SERVER_DOMAIN")

# === ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР ===

@lru_cache()
def get_settings() -> Settings:
    """
    Создает и кэширует экземпляр настроек.
    Используйте эту функцию для получения конфигурации в приложении.

    Пример использования:
        from app.config import get_settings

        settings = get_settings()
        print(settings.openai_api_key)
    """
    return Settings()


# Для удобства импорта
settings = get_settings()


# === ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ ===

def validate_all_settings() -> bool:
    """
    Проверяет все настройки при запуске приложения.
    Вызывайте в main.py для раннего обнаружения проблем.
    """
    try:
        current_settings = get_settings()

        # Проверяем критические настройки
        assert current_settings.openai_api_key, "OpenAI API key не установлен"
        assert current_settings.database_url, "Database URL не установлен"
        assert current_settings.yandex_api_key, "Yandex API key не установлен"

        print("✅ Все настройки корректны")
        return True

    except Exception as e:
        print(f"❌ Ошибка в настройках: {e}")
        return False


if __name__ == "__main__":
    # Для тестирования конфигурации
    validate_all_settings()
    current_settings = get_settings()
    print(f"Environment: {current_settings.environment}")
    print(f"Debug mode: {current_settings.debug}")
    print(f"Database configured: {'Yes' if current_settings.database_url else 'No'}")