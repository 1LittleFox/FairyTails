from fastapi import APIRouter, Query
from sqlmodel import select, desc

from app.database import SessionDep
from app.models import Collection, Story
from app.schemas import MainResponseSchema, CollectionPreviewResponseSchema, StoryPreviewResponseSchema
from app.services.conversion_time import seconds_to_hms
from app.i18n_config import get_supported_language, translate

router = APIRouter()

@router.get("/users/{user_id}/homes", response_model=MainResponseSchema)
async def get_home_data(
        user_id: str | None,
        session: SessionDep,
        lang: str = Query(default="en", description="Код языка интерфейса (ru, en, fr)")
        #Создать схему для ввода данных
):
    current_language = get_supported_language(lang)

    base_translations = {
        "compose_new_tale_text": translate("compose_new_tale", locale=current_language),
        "recent_label": translate("recent", locale=current_language),
        "my_collections_label": translate("my_collections", locale=current_language),
        "all_label": translate("all", locale=current_language)
    }

    if not user_id or user_id in ["null", "undefined", "anonymous"]:
        return MainResponseSchema(
            **base_translations,
            stories=[],
            collections=[],
            empty_message_recent=translate("recent_tales_empty", locale=current_language),
            empty_message_collections=translate("collections_empty", locale=current_language)
        )

    stmt_for_collection = select(Collection).where(Collection.user_id==user_id).order_by(
        desc(Collection.created_at))
    result_collection = await session.execute(stmt_for_collection)
    home_collections = result_collection.scalars().all()

    stmt_for_stories = select(Story).where(Story.user_id == user_id).order_by(
        desc(Story.created_at))
    result_stories = await session.execute(stmt_for_stories)
    home_stories = result_stories.scalars().all()

    recent_collections = [
        CollectionPreviewResponseSchema(
            id=collection.id,
            title=collection.title,
            url_image="Изображение коллекции",
        )
        for collection in home_collections
    ]

    recent_stories = [
        StoryPreviewResponseSchema(
            id=story.id,
            title=story.title,
            created_at=story.created_at,
            duration=seconds_to_hms(story.duration_seconds)
        )
        for story in home_stories
    ]

    # 8. Определяем нужны ли сообщения для пустых состояний
    empty_message_recent = None
    empty_message_collections = None

    if not recent_stories:
        empty_message_recent = translate("recent_tales_empty", locale=current_language)

    if not recent_collections:
        empty_message_collections = translate("collections_empty", locale=current_language)

    return MainResponseSchema(
        **base_translations,
        stories=recent_stories,
        collections=recent_collections,
        empty_message_recent=empty_message_recent,
        empty_message_collections=empty_message_collections
    )