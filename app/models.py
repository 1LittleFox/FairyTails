import uuid
from typing import Optional, List
from datetime import datetime, UTC

from sqlalchemy import TIMESTAMP
from sqlmodel import Field, SQLModel, Enum, Relationship
from sqlalchemy import Column, Text
from sqlalchemy.types import JSON
from app.schemas import EthnographyEnum, LanguageEnum, GenderEnum

class Base(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False
    )

class User(Base, table=True):
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True))
    )
    premium: bool = Field(default=False, nullable=False)

    # Relationship для связи с таблицей Коллекций
    collections: List["Collection"] = Relationship(back_populates="user")
    story: List["Story"] = Relationship(back_populates="user")

class Collection(Base, table=True):
    title: str = Field(max_length=50)
    total_Listening_time: int = Field(default=0)
    is_active: bool = Field(default=True)

    #foreign_key для связи Юзер и Коллекций
    user_id: uuid.UUID = Field(foreign_key="user.id")

    # Relationship для связи с таблицей Юзер
    user: User = Relationship(back_populates="collections")
    story: List["Story"] = Relationship(back_populates="collection")

class Story(Base, table=True):
    title: str = Field(max_length=50, nullable=False)
    content_story: str = Field(sa_column=Column(Text))
    audio_url: str = Field()
    duration_seconds: int = Field()

    #Поля анкеты которые нужны для продолжения
    age_in_months: int = Field(nullable=False) #Для расчета нового возраста
    ethnography: EthnographyEnum = Field(default=EthnographyEnum.ENGLISH_AND_IRISH,
                                         sa_column=Column(Enum(EthnographyEnum, name="ethnography_enum")))
    language: LanguageEnum = Field(default=LanguageEnum.ENGLISH,
                                         sa_column=Column(Enum(LanguageEnum, name="language_enum")))
    gender: GenderEnum = Field(default=GenderEnum.UNIVERSAL,
                                         sa_column=Column(Enum(GenderEnum, name="gender_enum")))
    interests: List[str] = Field(sa_column=Column(JSON))

    # foreign_key для связи Юзер и Коллекций
    user_id: uuid.UUID = Field(foreign_key="user.id")
    collection_id: uuid.UUID = Field(foreign_key="collection.id")

    # Relationship для связи с таблицей Юзер
    user: User = Relationship(back_populates="story")
    collection: Collection = Relationship(back_populates="story")
