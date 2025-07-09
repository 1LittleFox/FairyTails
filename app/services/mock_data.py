import uuid
from datetime import date, timedelta
from app.schemas import CollectionSchema, StoryPreviewSchema, CollectionsResponseSchema, UserCollectionsResponseSchema, \
    CollectionDetailsSchema


def format_duration(minutes: int) -> str:
    """Форматирует продолжительность в человекочитаемый вид"""
    if minutes < 60:
        return f"{minutes} минут"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours} час"
    return f"{hours} час {mins} минут"


def generate_mock_collections() -> CollectionsResponseSchema:
    # Моковые коллекции для главного экрана
    collections = [
        CollectionSchema(
            id=uuid.uuid4(),
            title_line1="Сказки про не спящего Дракона кешу",
            created_at=date(2025, 6, 19),
            duration_min=20,
            duration_text=format_duration(20)
        ),
        CollectionSchema(
            id=uuid.uuid4(),
            title_line1="Встающее солнце по утру",
            created_at=date(2025, 6, 19),
            duration_min=40,
            duration_text=format_duration(40)
        ),
        CollectionSchema(
            id=uuid.uuid4(),
            title_line1="Вини-Пух",
            created_at=date(2025, 6, 19),
            duration_min=40,
            duration_text=format_duration(40)
        )
    ]

    # Моковые сказки для главного экрана
    stories = [
        StoryPreviewSchema(
            id=uuid.uuid4(),
            title_line1="Король лев",
            created_at=date(2025, 6, 19),
            duration_min=10
        ),
        StoryPreviewSchema(
            id=uuid.uuid4(),
            title_line1="Бемби",
            created_at=date(2025, 6, 19),
            duration_min=10
        ),
        StoryPreviewSchema(
            id=uuid.uuid4(),
            title_line1="Леди и Бродяга",
            created_at=date(2025, 6, 19),
            duration_min=10
        ),
        StoryPreviewSchema(
            id=uuid.uuid4(),
            title_line1="Дамбо",
            created_at=date(2025, 6, 19),
            duration_min=10
        ),
        StoryPreviewSchema(
            id=uuid.uuid4(),
            title_line1="Зверополис",
            created_at=date(2025, 6, 19),
            duration_min=10
        )
    ]

    return CollectionsResponseSchema(
        collections=collections,
        stories=stories
    )


def generate_mock_user_collections() -> UserCollectionsResponseSchema:
    """Генерация данных для экрана 'Ваши сборники'"""
    collections = [
        CollectionSchema(
            id=uuid.uuid4(),
            title_line1="Сказки про не спящего Дракона кешу",
            created_at=date(2025, 6, 19),
            duration_min=20,
            duration_text="90 минут"
        ),
        CollectionSchema(
            id=uuid.uuid4(),
            title_line1="Встающее солнце по утру",
            created_at=date(2025, 6, 19),
            duration_min=40,
            duration_text="60 минут"
        ),
        CollectionSchema(
            id=uuid.uuid4(),
            title_line1="Вини-Пух",
            created_at=date(2025, 6, 19),
            duration_min=50,
            duration_text="50 минут"
        ),
        CollectionSchema(
            id=uuid.uuid4(),
            title_line1="Мечтательная Алина",
            created_at=date(2025, 6, 19),
            duration_min=20,
            duration_text="17 минут"
        )
    ]

    return UserCollectionsResponseSchema(collections=collections)

def generate_mock_collection_details(collection_id: uuid.UUID) -> CollectionDetailsSchema:
    """Генерация данных для конкретной коллекции"""
    # Определяем заголовок коллекции по ID
    if collection_id == uuid.UUID("a3b8d7f2-4c1e-4d89-b12f-8a9e0b1c5d6a"):
        title_line1 = "Сказки про не спящего Дракона кешу"
    elif collection_id == uuid.UUID("c75259e8-b9ed-483a-b73d-b242f3924fae"):
        title_line1 = "Встающее солнце по утру"
    else:
        title_line1 = "Вини-Пух"

    # Моковые сказки в коллекции
    stories = [
        StoryPreviewSchema(
            id=uuid.uuid4(),
            title_line1="Сказка соответствующая",
            created_at=date(2025, 6, 19),
            duration_min=10
        ),
        StoryPreviewSchema(
            id=uuid.uuid4(),
            title_line1="Сказка соответствующая",
            created_at=date(2025, 6, 19),
            duration_min=10
        ),
        StoryPreviewSchema(
            id=uuid.uuid4(),
            title_line1="Сказка соответствующая",
            created_at=date(2025, 6, 19),
            duration_min=10
        )
    ]

    return CollectionDetailsSchema(
        title_line1=title_line1,
        stories=stories
    )