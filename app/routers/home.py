import random

from fastapi import APIRouter
from datetime import datetime, timedelta
from app.schemas import HomePageData, Collection, FairyTale, ContinuationType

router = APIRouter()


# Генерация 15 сказок
def generate_fairy_tales():
    characters = ["Тимофей", "Алина", "Максим", "София", "Артём"]
    locations = [
        "Сад Вечных Тайн", "Остров Спящих Сокровищ", "Хрустальный Дворец",
        "Город Часовых Мастеров", "Королевство Зеркал", "Деревня Прядильщиков Облаков",
        "Лес Говорящих Деревьев", "Пещеры Хрустальных Гномов", "Озеро Лунного Света"
    ]
    adjectives = ["Задумчивый", "Отважный", "Мечтательный", "Любопытный", "Добрый", "Мудрый"]

    tales = []

    for i in range(1, 16):
        character = random.choice(characters)
        location = random.choice(locations)
        adjective = random.choice(adjectives)
        now = datetime.today() - timedelta(days=random.randint(0, 30))


        tale = FairyTale(
            title=f"{adjective} {character} в {location}",
            duration_minutes=random.randint(5, 20),
            created_at=now,
            continuation_type = ContinuationType.ORIGINAL
        )

        tales.append(tale)
    return tales


def generate_collections(tales):
    # Коллекции-продолжения (2 шт.)
    continuation_collections = []
    for i in range(7):
        base_tale = tales[i + 2]
        continuation = FairyTale(
            title=f"Продолжение: {base_tale.title}",
            duration_minutes=random.randint(8, 15),
            continuation_type=ContinuationType.CONTINUATION,
            base_tale_id=base_tale.id
        )

        collection = Collection(
            title=f"История {base_tale.title.split()[1]}",
            fairy_tales=[base_tale, continuation],
            is_continuation=True
        )
        continuation_collections.append(collection)
        tales.append(continuation)  # Добавляем продолжение в общий список

    return continuation_collections

@router.get("/home", response_model=HomePageData)
async def get_home_data():

    fairy_tales = generate_fairy_tales()
    collections = generate_collections(fairy_tales)

    # Последние 6 сказок для раздела "Недавние"
    recent_tales = sorted(
        fairy_tales,
        key=lambda x: x.created_at,
        reverse=True
    )[:6]

    return HomePageData(
        recent_tales=recent_tales,
        collections=collections
    )