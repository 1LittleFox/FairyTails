from fastapi import APIRouter, HTTPException, Query
import i18n
import os
from typing import Optional

# Настройка i18n
i18n.set('locale', 'en')  # английский по умолчанию
i18n.set('fallback', 'en')
i18n.load_path.append('app/locales')  # папка с переводами

router = APIRouter()

# Поддерживаемые языки
SUPPORTED_LANGUAGES = ['ru', 'en', 'fr']

def validate_language(lang: str) -> str:
    """Валидация и fallback для языка"""
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return 'en'  # fallback на английский

def translate_with_error_handling(key: str, locale: str) -> str:
    """Перевод с обработкой отсутствующих переводов"""
    try:
        translation = i18n.t(key, locale=locale)
        # Проверяем, что перевод не равен ключу (что означает отсутствие перевода)
        if translation == key:
            raise HTTPException(
                status_code=500,
                detail=f"Translation missing for key '{key}' in locale '{locale}'"
            )
        return translation
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Translation error for key '{key}': {str(e)}"
        )

@router.get("/questionnaire_options")
async def get_options(lang: Optional[str] = Query('en', description="Language code (ru, en, fr)")):
    # Валидация языка с fallback
    validated_lang = validate_language(lang)

    try:
        # Переводим этнографические группы
        ethnography_data = []
        ethnography_keys = [
            "germanic", "slavic", "caucasian", "turkic", "french",
            "scandinavian", "english_irish", "italian", "spanish_portuguese",
            "greek", "persian", "indian", "chinese", "japanese", "jewish"
        ]

        for key in ethnography_keys:
            ethnography_data.append({
                "name": translate_with_error_handling(f"ethnography.{key}.name", validated_lang),
                "description": translate_with_error_handling(f"ethnography.{key}.description", validated_lang)
            })

        # Переводим гендеры
        genders = [
            translate_with_error_handling("genders.boy", validated_lang),
            translate_with_error_handling("genders.girl", validated_lang),
            translate_with_error_handling("genders.universal", validated_lang)
        ]

        # Переводим категории интересов
        categories = []
        category_keys = [
            "animals", "transport", "magic", "princesses", "superheroes",
            "astronauts", "mythical_creatures", "ordinary_people", "other"
        ]

        for i, key in enumerate(category_keys, 1):
            categories.append({
                "id": i,
                "name": translate_with_error_handling(f"interests.categories.{key}", validated_lang)
            })

        # Переводим подкатегории
        subcategories = {
            "1": [  # Животные
                {"id": 101, "name": translate_with_error_handling("interests.subcategories.cats", validated_lang)},
                {"id": 102, "name": translate_with_error_handling("interests.subcategories.dogs", validated_lang)},
                {"id": 103, "name": translate_with_error_handling("interests.subcategories.dinosaurs", validated_lang)},
                {"id": 104,
                 "name": translate_with_error_handling("interests.subcategories.forest_animals", validated_lang)}
            ],
            "2": [  # Транспорт
                {"id": 201, "name": translate_with_error_handling("interests.subcategories.cars", validated_lang)},
                {"id": 202, "name": translate_with_error_handling("interests.subcategories.trains", validated_lang)},
                {"id": 203, "name": translate_with_error_handling("interests.subcategories.planes", validated_lang)}
            ],
            "3": [  # Магия
                {"id": 301,
                 "name": translate_with_error_handling("interests.subcategories.sorceresses", validated_lang)},
                {"id": 302, "name": translate_with_error_handling("interests.subcategories.fairies", validated_lang)},
                {"id": 303, "name": translate_with_error_handling("interests.subcategories.planes", validated_lang)}
                # Похоже на ошибку в оригинале
            ],
            "4": [  # Принцессы
                {"id": 401,
                 "name": translate_with_error_handling("interests.subcategories.rebel_princess", validated_lang)},
                {"id": 402,
                 "name": translate_with_error_handling("interests.subcategories.warrior_princess", validated_lang)},
                {"id": 403,
                 "name": translate_with_error_handling("interests.subcategories.exiled_princess", validated_lang)}
            ],
            "5": [  # Супергерои
                {"id": 501, "name": translate_with_error_handling("interests.subcategories.iron_man", validated_lang)},
                {"id": 502, "name": translate_with_error_handling("interests.subcategories.superman", validated_lang)},
                {"id": 503, "name": translate_with_error_handling("interests.subcategories.batman", validated_lang)},
                {"id": 504, "name": translate_with_error_handling("interests.subcategories.spiderman", validated_lang)},
                {"id": 505,
                 "name": translate_with_error_handling("interests.subcategories.wonder_woman", validated_lang)}
            ],
            "6": [  # Космонавты
                {"id": 601,
                 "name": translate_with_error_handling("interests.subcategories.test_astronauts", validated_lang)},
                {"id": 602,
                 "name": translate_with_error_handling("interests.subcategories.explorer_astronauts", validated_lang)}
            ],
            "7": [  # Сказочные существа
                {"id": 701, "name": translate_with_error_handling("interests.subcategories.dragons", validated_lang)},
                {"id": 702, "name": translate_with_error_handling("interests.subcategories.griffins", validated_lang)},
                {"id": 703, "name": translate_with_error_handling("interests.subcategories.pegasus", validated_lang)},
                {"id": 704, "name": translate_with_error_handling("interests.subcategories.phoenix", validated_lang)}
            ],
            "8": [  # Обычные люди
                {"id": 801, "name": translate_with_error_handling("interests.subcategories.child", validated_lang)},
                {"id": 802, "name": translate_with_error_handling("interests.subcategories.father", validated_lang)},
                {"id": 803, "name": translate_with_error_handling("interests.subcategories.mother", validated_lang)}
            ]
        }

        # Переводим soft skills
        soft_skills_keys = [
            "self_preservation", "positivity", "empathy", "creativity", "curiosity",
            "courage", "stress_management", "self_motivation", "productivity",
            "diligence", "justice", "forgiveness", "friendship", "prosocial_behavior",
            "leadership", "confidence", "persuasion", "team_spirit", "flexibility", "etiquette"
        ]

        soft_skills = []
        for key in soft_skills_keys:
            soft_skills.append(translate_with_error_handling(f"soft_skills.{key}", validated_lang))

        # Переводим языки
        languages = [
            translate_with_error_handling("languages.russian", validated_lang),
            translate_with_error_handling("languages.english", validated_lang),
            translate_with_error_handling("languages.french", validated_lang)
        ]

        return {
            "ethnography": ethnography_data,
            "genders": genders,
            "interests": {
                "categories": categories,
                "subcategories": subcategories
            },
            "soft_skills": soft_skills,
            "languages": languages
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Localization error: {str(e)}")