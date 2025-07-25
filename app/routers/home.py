from fastapi import APIRouter
from sqlmodel import select, desc

from app.database import SessionDep
from app.models import Collection, Story
from app.schemas import MainResponseSchema, CollectionPreviewResponseSchema, StoryPreviewResponseSchema
from app.services.conversion_time import seconds_to_hms

router = APIRouter()

@router.get("/users/{user_id}/home", response_model=MainResponseSchema)
async def get_home_data(
        user_id: str | None,
        session: SessionDep
        #Создать схему для ввода данных
):
    if not user_id or user_id in ["null", "undefined", "anonymous"]:
        return MainResponseSchema(
            collections=[],
            stories=[],
            message1="Здесь будут отображаться прослушенные недавно сказки"
                     "Сочините первую сказку, начните слушать, и она появится здесь",
            message2="Сочините вашу первую сказку и сборник создастся автоматически"
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


    return MainResponseSchema(
        stories=recent_stories,
        collections=recent_collections,
        message1="Недавние",
        message2="Мои сборники"
    )