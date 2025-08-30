from fastapi import APIRouter, HTTPException, Query
import i18n
import os
from typing import Optional

from markupsafe import soft_str

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

        for i, key in enumerate(ethnography_keys, 1):
            ethnography_data.append({
                "id": i,
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
            "animals_nature", "transport_tech", "people_professions", "fantasy_fairy",
            "superheroes_adventures", "natural_worlds", "magic_artifacts",
            "friends_community", "hobbies_interests"
        ]

        for i, key in enumerate(category_keys, 1):
            categories.append({
                "id": i,
                "name": translate_with_error_handling(f"interests.categories.{key}", validated_lang)
            })

        # Переводим подкатегории с привязанными интересами
        subcategories = {
            "1": [  # Животные и природа
                {
                    "id": 101,
                    "name": translate_with_error_handling("interests.subcategories.pets", validated_lang),
                    "interests": [
                        {"id": 10101,
                         "name": translate_with_error_handling("interests.detailed_interests.cats", validated_lang)},
                        {"id": 10102,
                         "name": translate_with_error_handling("interests.detailed_interests.dogs", validated_lang)},
                        {"id": 10103,
                         "name": translate_with_error_handling("interests.detailed_interests.rabbits", validated_lang)},
                        {"id": 10104, "name": translate_with_error_handling("interests.detailed_interests.hamsters",
                                                                            validated_lang)},
                        {"id": 10105, "name": translate_with_error_handling("interests.detailed_interests.guinea_pigs",
                                                                            validated_lang)},
                        {"id": 10106,
                         "name": translate_with_error_handling("interests.detailed_interests.fish", validated_lang)}
                    ]
                },
                {
                    "id": 102,
                    "name": translate_with_error_handling("interests.subcategories.forest_animals", validated_lang),
                    "interests": [
                        {"id": 10201, "name": translate_with_error_handling("interests.detailed_interests.rabbits_wild",
                                                                            validated_lang)},
                        {"id": 10202,
                         "name": translate_with_error_handling("interests.detailed_interests.foxes", validated_lang)},
                        {"id": 10203, "name": translate_with_error_handling("interests.detailed_interests.squirrels",
                                                                            validated_lang)},
                        {"id": 10204,
                         "name": translate_with_error_handling("interests.detailed_interests.bears", validated_lang)},
                        {"id": 10205,
                         "name": translate_with_error_handling("interests.detailed_interests.deer", validated_lang)},
                        {"id": 10206, "name": translate_with_error_handling("interests.detailed_interests.hedgehogs",
                                                                            validated_lang)}
                    ]
                },
                {
                    "id": 103,
                    "name": translate_with_error_handling("interests.subcategories.african_exotic", validated_lang),
                    "interests": [
                        {"id": 10301,
                         "name": translate_with_error_handling("interests.detailed_interests.lions", validated_lang)},
                        {"id": 10302, "name": translate_with_error_handling("interests.detailed_interests.elephants",
                                                                            validated_lang)},
                        {"id": 10303, "name": translate_with_error_handling("interests.detailed_interests.giraffes",
                                                                            validated_lang)},
                        {"id": 10304,
                         "name": translate_with_error_handling("interests.detailed_interests.zebras", validated_lang)},
                        {"id": 10305,
                         "name": translate_with_error_handling("interests.detailed_interests.monkeys", validated_lang)}
                    ]
                },
                {
                    "id": 104,
                    "name": translate_with_error_handling("interests.subcategories.dinosaurs", validated_lang),
                    "interests": [
                        {"id": 10401,
                         "name": translate_with_error_handling("interests.detailed_interests.tyrannosaurus",
                                                               validated_lang)},
                        {"id": 10402, "name": translate_with_error_handling("interests.detailed_interests.triceratops",
                                                                            validated_lang)},
                        {"id": 10403, "name": translate_with_error_handling("interests.detailed_interests.stegosaurus",
                                                                            validated_lang)},
                        {"id": 10404, "name": translate_with_error_handling("interests.detailed_interests.brontosaurus",
                                                                            validated_lang)}
                    ]
                },
                {
                    "id": 105,
                    "name": translate_with_error_handling("interests.subcategories.sea_creatures", validated_lang),
                    "interests": [
                        {"id": 10501, "name": translate_with_error_handling("interests.detailed_interests.dolphins",
                                                                            validated_lang)},
                        {"id": 10502,
                         "name": translate_with_error_handling("interests.detailed_interests.whales", validated_lang)},
                        {"id": 10503,
                         "name": translate_with_error_handling("interests.detailed_interests.sharks", validated_lang)},
                        {"id": 10504, "name": translate_with_error_handling("interests.detailed_interests.starfish",
                                                                            validated_lang)},
                        {"id": 10505,
                         "name": translate_with_error_handling("interests.detailed_interests.turtles", validated_lang)}
                    ]
                },
                {
                    "id": 106,
                    "name": translate_with_error_handling("interests.subcategories.birds", validated_lang),
                    "interests": [
                        {"id": 10601,
                         "name": translate_with_error_handling("interests.detailed_interests.parrots", validated_lang)},
                        {"id": 10602,
                         "name": translate_with_error_handling("interests.detailed_interests.owls", validated_lang)},
                        {"id": 10603, "name": translate_with_error_handling("interests.detailed_interests.penguins",
                                                                            validated_lang)},
                        {"id": 10604, "name": translate_with_error_handling("interests.detailed_interests.flamingos",
                                                                            validated_lang)},
                        {"id": 10605,
                         "name": translate_with_error_handling("interests.detailed_interests.ducks", validated_lang)}
                    ]
                },
                {
                    "id": 107,
                    "name": translate_with_error_handling("interests.subcategories.insects_small", validated_lang),
                    "interests": [
                        {"id": 10701, "name": translate_with_error_handling("interests.detailed_interests.butterflies",
                                                                            validated_lang)},
                        {"id": 10702, "name": translate_with_error_handling("interests.detailed_interests.ladybugs",
                                                                            validated_lang)},
                        {"id": 10703,
                         "name": translate_with_error_handling("interests.detailed_interests.bees", validated_lang)},
                        {"id": 10704, "name": translate_with_error_handling("interests.detailed_interests.fireflies",
                                                                            validated_lang)}
                    ]
                }
            ],
            "2": [  # Транспорт и техника
                {
                    "id": 201,
                    "name": translate_with_error_handling("interests.subcategories.cars", validated_lang),
                    "interests": [
                        {"id": 20101,
                         "name": translate_with_error_handling("interests.detailed_interests.passenger_cars",
                                                               validated_lang)},
                        {"id": 20102, "name": translate_with_error_handling("interests.detailed_interests.sports_cars",
                                                                            validated_lang)},
                        {"id": 20103, "name": translate_with_error_handling("interests.detailed_interests.police_cars",
                                                                            validated_lang)}
                    ]
                },
                {
                    "id": 202,
                    "name": translate_with_error_handling("interests.subcategories.trucks_special", validated_lang),
                    "interests": [
                        {"id": 20201, "name": translate_with_error_handling("interests.detailed_interests.fire_trucks",
                                                                            validated_lang)},
                        {"id": 20202, "name": translate_with_error_handling("interests.detailed_interests.excavators",
                                                                            validated_lang)},
                        {"id": 20203, "name": translate_with_error_handling("interests.detailed_interests.tractors",
                                                                            validated_lang)},
                        {"id": 20204,
                         "name": translate_with_error_handling("interests.detailed_interests.cranes", validated_lang)}
                    ]
                },
                {
                    "id": 203,
                    "name": translate_with_error_handling("interests.subcategories.trains", validated_lang),
                    "interests": [
                        {"id": 20301,
                         "name": translate_with_error_handling("interests.detailed_interests.passenger_trains",
                                                               validated_lang)},
                        {"id": 20302,
                         "name": translate_with_error_handling("interests.detailed_interests.steam_engines",
                                                               validated_lang)}
                    ]
                },
                {"id": 204,
                 "name": translate_with_error_handling("interests.subcategories.planes_helicopters", validated_lang)},
                {
                    "id": 205,
                    "name": translate_with_error_handling("interests.subcategories.ships_boats", validated_lang),
                    "interests": [
                        {"id": 20501,
                         "name": translate_with_error_handling("interests.detailed_interests.ferries", validated_lang)},
                        {"id": 20502, "name": translate_with_error_handling("interests.detailed_interests.submarines",
                                                                            validated_lang)},
                        {"id": 20503,
                         "name": translate_with_error_handling("interests.detailed_interests.yachts", validated_lang)}
                    ]
                },
                {"id": 206,
                 "name": translate_with_error_handling("interests.subcategories.spaceships_rockets", validated_lang)},
                {"id": 207, "name": translate_with_error_handling("interests.subcategories.robots", validated_lang)}
            ],
            "3": [  # Люди и профессии
                {"id": 301,
                 "name": translate_with_error_handling("interests.subcategories.ordinary_children", validated_lang)},
                {"id": 302, "name": translate_with_error_handling("interests.subcategories.family", validated_lang)},
                {
                    "id": 303,
                    "name": translate_with_error_handling("interests.subcategories.helper_professions", validated_lang),
                    "interests": [
                        {"id": 30301, "name": translate_with_error_handling("interests.detailed_interests.firefighters",
                                                                            validated_lang)},
                        {"id": 30302,
                         "name": translate_with_error_handling("interests.detailed_interests.doctors", validated_lang)},
                        {"id": 30303, "name": translate_with_error_handling("interests.detailed_interests.teachers",
                                                                            validated_lang)},
                        {"id": 30304, "name": translate_with_error_handling("interests.detailed_interests.builders",
                                                                            validated_lang)},
                        {"id": 30305,
                         "name": translate_with_error_handling("interests.detailed_interests.veterinarians",
                                                               validated_lang)},
                        {"id": 30306,
                         "name": translate_with_error_handling("interests.detailed_interests.cooks", validated_lang)},
                        {"id": 30307,
                         "name": translate_with_error_handling("interests.detailed_interests.police_officers",
                                                               validated_lang)},
                        {"id": 30308,
                         "name": translate_with_error_handling("interests.detailed_interests.mail_carriers",
                                                               validated_lang)}
                    ]
                },
                {"id": 304,
                 "name": translate_with_error_handling("interests.subcategories.school_kindergarten", validated_lang)}
            ],
            "4": [  # Фантастические и сказочные персонажи
                {"id": 401,
                 "name": translate_with_error_handling("interests.subcategories.princes_princesses", validated_lang)},
                {"id": 402,
                 "name": translate_with_error_handling("interests.subcategories.fairies_wizards", validated_lang)},
                {"id": 403,
                 "name": translate_with_error_handling("interests.subcategories.good_dragons", validated_lang)},
                {"id": 404, "name": translate_with_error_handling("interests.subcategories.unicorns", validated_lang)},
                {"id": 405, "name": translate_with_error_handling("interests.subcategories.pegasus", validated_lang)},
                {"id": 406, "name": translate_with_error_handling("interests.subcategories.mermaids", validated_lang)},
                {"id": 407,
                 "name": translate_with_error_handling("interests.subcategories.gnomes_elves", validated_lang)},
                {"id": 408,
                 "name": translate_with_error_handling("interests.subcategories.fairy_animals", validated_lang)}
            ],
            "5": [  # Супергерои и приключения
                {"id": 501,
                 "name": translate_with_error_handling("interests.subcategories.superheroes", validated_lang)},
                {"id": 502,
                 "name": translate_with_error_handling("interests.subcategories.astronaut_explorers", validated_lang)},
                {"id": 503,
                 "name": translate_with_error_handling("interests.subcategories.good_pirates", validated_lang)},
                {"id": 504,
                 "name": translate_with_error_handling("interests.subcategories.treasure_hunters", validated_lang)},
                {"id": 505,
                 "name": translate_with_error_handling("interests.subcategories.spies_detectives", validated_lang)}
            ],
            "6": [  # Природные миры и локации
                {"id": 601,
                 "name": translate_with_error_handling("interests.subcategories.forests_jungles", validated_lang)},
                {"id": 602,
                 "name": translate_with_error_handling("interests.subcategories.mountains_volcanoes", validated_lang)},
                {"id": 603,
                 "name": translate_with_error_handling("interests.subcategories.underwater_world", validated_lang)},
                {"id": 604,
                 "name": translate_with_error_handling("interests.subcategories.space_planets", validated_lang)},
                {"id": 605,
                 "name": translate_with_error_handling("interests.subcategories.fields_meadows", validated_lang)},
                {"id": 606,
                 "name": translate_with_error_handling("interests.subcategories.caves_groves", validated_lang)}
            ],
            "7": [  # Магия, артефакты и предметы
                {"id": 701,
                 "name": translate_with_error_handling("interests.subcategories.enchanted_castles", validated_lang)},
                {"id": 702,
                 "name": translate_with_error_handling("interests.subcategories.magic_forests", validated_lang)},
                {"id": 703,
                 "name": translate_with_error_handling("interests.subcategories.treasures_hoards", validated_lang)},
                {"id": 704,
                 "name": translate_with_error_handling("interests.subcategories.magic_wands", validated_lang)},
                {"id": 705,
                 "name": translate_with_error_handling("interests.subcategories.flying_objects", validated_lang)}
            ],
            "8": [  # Друзья, отношения и сообщество
                {"id": 801,
                 "name": translate_with_error_handling("interests.subcategories.friends_company", validated_lang)},
                {"id": 802,
                 "name": translate_with_error_handling("interests.subcategories.pet_companions", validated_lang)},
                {"id": 803,
                 "name": translate_with_error_handling("interests.subcategories.playground", validated_lang)},
                {"id": 804, "name": translate_with_error_handling("interests.subcategories.school_kindergarten_life",
                                                                  validated_lang)},
                {"id": 805,
                 "name": translate_with_error_handling("interests.subcategories.holidays_parties", validated_lang)}
            ],
            "9": [  # Хобби и увлечения
                {"id": 901,
                 "name": translate_with_error_handling("interests.subcategories.music_singing", validated_lang)},
                {"id": 902, "name": translate_with_error_handling("interests.subcategories.dancing", validated_lang)},
                {"id": 903,
                 "name": translate_with_error_handling("interests.subcategories.drawing_creativity", validated_lang)},
                {
                    "id": 904,
                    "name": translate_with_error_handling("interests.subcategories.sports_games", validated_lang),
                    "interests": [
                        {"id": 90401, "name": translate_with_error_handling("interests.detailed_interests.football",
                                                                            validated_lang)},
                        {"id": 90402,
                         "name": translate_with_error_handling("interests.detailed_interests.cycling", validated_lang)},
                        {"id": 90403, "name": translate_with_error_handling("interests.detailed_interests.gymnastics",
                                                                            validated_lang)}
                    ]
                },
                {"id": 905, "name": translate_with_error_handling("interests.subcategories.cooking", validated_lang)}
            ]
        }

        # Переводим soft skills
        soft_skills = []
        soft_skills_keys = [
            "self_preservation", "positivity", "empathy", "creativity", "curiosity",
            "courage", "stress_management", "self_motivation", "productivity",
            "diligence", "justice", "forgiveness", "friendship", "prosocial_behavior",
            "leadership", "confidence", "persuasion", "team_spirit", "flexibility", "etiquette"
        ]

        for i, key in enumerate(soft_skills_keys, 1):
            soft_skills.append({
                "id": i,
                "name": translate_with_error_handling(f"soft_skills.{key}", validated_lang)
            })

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
            "languages": languages,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Localization error: {str(e)}")