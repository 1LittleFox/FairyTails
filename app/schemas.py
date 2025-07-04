from enum import Enum
from datetime import datetime
from traceback import print_tb
from typing import List, Optional
from pydantic import BaseModel, Field, conint, constr, validator
from uuid import uuid4


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

class ContinuationType(str, Enum):
    ORIGINAL = "original"
    CONTINUATION = "continuation"

class FairyTale(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    created_at: datetime = Field(default_factory=datetime.today)
    duration_minutes: int
    continuation_type: ContinuationType = Field(ContinuationType.ORIGINAL)
    base_tale_id: Optional[str] = None  # Для продолжений - ID оригинальной сказки
    preview_image: Optional[str] = None


class Collection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    created_at: datetime = Field(default_factory=datetime.now)
    fairy_tales: List[FairyTale] = Field(
        default_factory=list,
        description="Список сказок в сборнике"
    )
    is_continuation: bool = False  # Флаг, что сборник создан для продолжения
    preview_image: Optional[str] = None

    @property
    def total_duration_minutes(self) -> int:
        """Вычисляемое свойство: общая длительность сборника"""
        return sum(tale.duration_minutes for tale in self.fairy_tales)

    @property
    def tales_count(self) -> int:
        """Вычисляемое свойство: количество сказок"""
        return len(self.fairy_tales)


class HomePageData(BaseModel):
    recent_tales: List[FairyTale]
    collections: List[Collection]