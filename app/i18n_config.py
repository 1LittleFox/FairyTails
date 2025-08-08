import i18n
import os
from typing import List

# Поддерживаемые языки
SUPPORTED_LANGUAGES: List[str] = ['en', 'ru', 'fr']
DEFAULT_LANGUAGE: str = 'en'


def setup_i18n():
    """Настройка i18n для приложения"""
    # Получаем директорию где находится текущий файл (app/)
    current_dir = os.path.dirname(__file__)
    # Путь к папке locales внутри app/
    locales_path = os.path.join(current_dir, 'locales')

    # Настройка i18n
    i18n.set('filename_format', '{locale}.{format}')
    i18n.set('file_format', 'json')
    i18n.set('fallback', DEFAULT_LANGUAGE)
    i18n.set('skip_locale_root_data', True)
    i18n.load_path.append(locales_path)


def get_supported_language(lang_code: str) -> str:
    """
    Проверяет поддерживаться ли язык и возвращает корректный код

    Args:
        lang_code: Код языка от клиента

    Returns:
        Поддерживаемый код языка или дефолтный
    """
    if not lang_code:
        return DEFAULT_LANGUAGE

    # Приводим к нижнему регистру и берем только первые 2 символа
    normalized_lang = lang_code.lower()[:2]

    return normalized_lang if normalized_lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def translate(key: str, locale: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Функция для перевода текста

    Args:
        key: Ключ перевода
        locale: Код языка
        **kwargs: Дополнительные параметры для интерполяции

    Returns:
        Переведенный текст
    """
    try:
        return i18n.t(key, locale=locale, **kwargs)
    except Exception as e:
        # В случае ошибки возвращаем ключ или английский перевод
        print(f"Translation error for key '{key}' and locale '{locale}': {e}")
        if locale != DEFAULT_LANGUAGE:
            return i18n.t(key, locale=DEFAULT_LANGUAGE, **kwargs)
        return key