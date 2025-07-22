# schemas.py
import re
import uuid
from enum import Enum
from datetime import datetime, date
from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field, conint, validator, UUID4
from uuid import uuid4


class GenderEnum(str, Enum):
    BOY = "Мальчик"
    GIRL = "Девочка"
    UNIVERSAL = "Универсальный герой"

class InterestCategory(str, Enum):
    ANIMALS = "Животные"
    VEHICLES = "Транспорт"
    MAGIK = "Магия"
    PRINCESSES = "Принцессы"
    SUPERHEROES = "Супергерои"
    ASTRONAUTS = "Космонавты"
    FABULOUS_CREATURES = "Сказочные существа"
    ORDINARY_PEOPLE = "Обычные дети/взрослые"
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


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class EthnographyEnum(str, Enum):
    GERMAN = "Германские"
    SLAVIC = "Славянские"
    CAUCASIAN = "Кавказские"
    TURKIC = "Тюркские"
    FRENCH = "Французские"
    SCANDINAVIAN = "Скандинавские"
    ENGLISH_AND_IRISH = "Английские и Ирландские"
    ITALIAN = "Итальянские"
    SPANISH_AND_PORTUGUESE = "Испанские и Португальские"
    GREEK = "Греческие"
    PERSIAN = "Персидские"
    INDIAN = "Индийские"
    CHINESE = "Китайские"
    JAPANESE = "Японские"
    JEWISH = "Еврейские"


class LanguageEnum(str, Enum):
    RUSSIAN = "русском"
    ENGLISH = "английском"
    FRENCH = "французском"

class Questionnaire(BaseModel):
    age_years: conint(ge=0, le=99) = Field(..., description="Возраст в полных годах")
    age_months: conint(ge=0, le=11) = Field(..., description="Месяцы")

    interest_category: InterestCategory = Field(
        ...,
        description="Категории интересов ребёнка"
    )

    subcategories: List[str] = Field(
        ...,
        description="Конкретные интересы внутри выбранной категории"
    )

    target_words: List[str] = Field(
        ...,
        description="Целевые слова/звуки для включения в сказку"
    )

    story_duration_minutes: conint(ge=1, le=60) = Field(
        ...,
        description="Длительность сказки в минутах (не более 60)"
    )

    soft_skills: SoftSkillEnum = Field(
        ...,
        description="Развиваемые мягкие навыки (не более 3)"
    )

    ethnography_choice: EthnographyEnum = Field(
        ...,
        description="Этнографическая характеристика сказки"
    )

    language: LanguageEnum = Field(
        default=LanguageEnum.ENGLISH,
        description="Язык сказки"
    )

    gender: GenderEnum = Field(
        ...,
        description="Пол ребёнка"
    )


    @validator('subcategories', always=True)
    def validate_subcategories(cls, subcategory_values, values):
        """Базовая валидация подкатегорий"""
        if len(subcategory_values) < 1:
            raise ValueError("Нужно выбрать хотя бы один интерес")

        for item in subcategory_values:
            if not (isinstance(item, str) and item.strip()):
                raise ValueError("Отправлены пустые значения")

        if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\-]+$", subcategory_values[0]):
            raise ValueError("Используйте только буквы и дефис")

        category = values.get('interest_category')
        # Для MVP проверяем только общие ограничения

        if category == InterestCategory.OTHER:
            if len(subcategory_values) != 1:
                raise ValueError("Нужно выбрать один интерес")
            if len(subcategory_values[0].split()) > 1:
                raise ValueError("Для категории 'Другое' допустимо только одно слово")

        return subcategory_values

    @validator('target_words', always=True)
    def validate_target_words(cls, target_words):
        if len(target_words) < 1:
            raise ValueError("Минимум 1 слово")
        if len(target_words) > 3:
            raise ValueError("Максимум 3 слова")
        return target_words



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

"""Схемы данных для отправки на фронт"""

class EthnographyOption(BaseModel):
    name: str
    description: str

class InterestSubcategories(BaseModel):
    id: int
    name: str

class InterestCategories(BaseModel):
    id: int
    name: str

class OptionsResponse(BaseModel):
    ethnography: List[EthnographyOption]
    genders: List[str]
    interests: Dict[str, List[Union[InterestCategories, Dict[str, List[InterestSubcategories]]]]]
    soft_skills: List[str]
    languages: List[str]

# Модели для моков
class CollectionSchema(BaseModel):
    title: str
    created_at: datetime
    duration: str

class StoryPreviewSchema(BaseModel):
    id: UUID4
    title_line1: str  # Первая строка названия
    created_at: str
    duration_min: int

class CollectionsResponseSchema(BaseModel):
    collections: list[CollectionSchema]
    stories: list[StoryPreviewSchema]

class UserCollectionsResponseSchema(BaseModel):
    collections: list[CollectionSchema]  # Для экрана "Ваши сборники"

class CollectionDetailsSchema(BaseModel):
    title_line1: str
    stories: list[StoryPreviewSchema]

# Request/Response models
class UserAccessRequest(BaseModel):
    user_id: Optional[uuid.UUID] = None

class StoryGenerationResponse(BaseModel):
    user_id: uuid.UUID
    created_at: datetime
    content: str
    url: str