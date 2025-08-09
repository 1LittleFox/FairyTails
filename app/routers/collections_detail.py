from fastapi import APIRouter
from sqlmodel import select, desc

from app.database import SessionDep
from app.models import Collection, Story
from app.schemas import CollectionDetailsSchema, StoryPreviewResponseSchema
from app.services.conversion_time import seconds_to_minutes

router = APIRouter()


@router.get("/collections/{id}", response_model=CollectionDetailsSchema)
async def get_collection_details(
        id: str | None,
        session: SessionDep
):
    stmt_for_title = select(Collection.title).where(Collection.id == id)
    result = await session.execute(stmt_for_title)
    title_collection = result.scalars().first()

    collection_detail = select(Story).where(Story.collection_id == id).order_by(desc(Story.created_at))
    result_collection_detail = await session.execute(collection_detail)
    all_fairy_tails_in_collection = result_collection_detail.scalars().all()

    fairy_tails = [
        StoryPreviewResponseSchema(
            id=story.id,
            title=story.title,
            preview_image="Изображение коллекции",
            created_at=story.created_at,
            duration=seconds_to_minutes(story.duration_seconds)
        )
        for story in all_fairy_tails_in_collection
    ]

    return CollectionDetailsSchema(
        title=title_collection,
        stories=fairy_tails
    )