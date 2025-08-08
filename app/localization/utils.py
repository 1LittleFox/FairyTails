from app.localization.constants import DEFAULT_LANGUAGE

def get_translation(locale: str, fallback_locale: str = DEFAULT_LANGUAGE):
    return TRANSLATIONS.get(locale, TRANSLATIONS[fallback_locale])