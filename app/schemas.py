from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, conint, constr, validator

class GenderEnum(str, Enum):
    BOY = "Мальчик"
    GIRL = "Девочка"
    UNIVERSAL = "Универсальный герой"

class InterestCategory(str, Enum):
    ANIMALS = "Животные"
    VEHICLES = "Транспорт"
    PRINCESSES = "Принцессы/Волшебницы"
    SUPERHEROES = "Супергерои/Космонавты"
    FABULOUS_CREATURES = "Волшебные существа"
    ORDINARY_PEOPLE = "Обычные дети/Люди"
    OTHER = "Другое"

class SoftSkillEnum(str, Enum):
    SELF_PRESERVATION = "Самосохранение и безопасность"
    POSITIVITY = "Позитивность"
    EMPATHY = "Эмпатия и сострадание"
    CREATIVITY = "Креативность"
    CURIOSITY = "Любознательность"
    COURAGE = "Смелость"
    STRESS_MANAGEMENT = "Управление стрессом"
    SELF_MOTIVATION = "Самомотивация"
    PRODUCTIVITY = "Продуктивность"
    EXTRA_EFFORT = "Сверхусердие"
    JUSTICE = "Справедливость"
    FORGIVENESS = "Умение прощать"
    FRIENDSHIP = "Дружба"
    PROSOCIAL_BEHAVIOR = "Просоциальное поведение"
    LEADERSHIP = "Лидерство"
    CONFIDENCE = "Уверенность"
    PERSUASION = "Убеждение"
    TEAM_SPIRIT = "Командный дух"
    FLEXIBILITY = "Гибкость"
    ETIQUETTE = "Этикет"

class EthnographyEnum(str, Enum):
    RUSSIAN = "Русская"
    EUROPEAN = "Европейская"
    ORIENTAL = "Восточная"
    AFRICAN = "Африканская"

class LanguageEnum(str, Enum):
    RUSSIAN = "русском"
    ENGLISH = "английском"
    SPANISH = "испанском"
    GERMAN = "немецком"

class Questionnaire(BaseModel):
    language: LanguageEnum = Field(
        default=LanguageEnum.ENGLISH,
        description="Язык сказки"
    )
    age_years: conint(ge=0) = Field(..., description="Возраст в полных годах")
    age_months: conint(ge=0, le=11) = Field(..., description="Месяцы")
    gender: GenderEnum = Field(..., description="Пол ребёнка")
    interests: List[InterestCategory] = Field(
        ...,
        description="Категории интересов ребёнка"
    )
    specific_interests: Optional[List[str]] = Field(
        None,
        description="Конкретные интересы внутри категорий"
    )
    other_interest: Optional[str] = Field(
        None,
        max_length=100,
        description="Другой интерес (указать)"
    )
    target_words: List[constr(min_length=1, max_length=20)] = Field(
        ...,
        description="Целевые слова/звуки для включения в сказку"
    )
    soft_skills: List[SoftSkillEnum] = Field(
        ...,
        description="Развиваемые мягкие навыки (не более 3)"
    )
    story_duration_minutes: conint(ge=1, le=60) = Field(
        ...,
        description="Длительность сказки в минутах (не более 60)"
    )
    ethnography_choice: EthnographyEnum = Field(
        ...,
        description="Этнографическая характеристика сказки"
    )

    @validator('other_interest', always=True)
    def validate_other_interest(cls, v, values):
        if 'interests' in values and InterestCategory.OTHER in values['interests'] and not v:
            raise ValueError(
                "Требуется указать другой интерес, когда выбрана категория 'Другое'"
            )
        return v

# class FairyTaleRequest(BaseModel):
#     prompt: str = Field(..., max_length=5000, description="Полный промпт для генерации сказки")
#
# class FairyTaleResponse(BaseModel):
#     status: str = Field(..., example="success")
#     fairy_tale: str = Field(..., description="Сгенерированный текст сказки")
#     model: str = Field(..., description="Использованная модель ИИ")
#     usage: dict = Field(..., description="Информация об использовании токенов")