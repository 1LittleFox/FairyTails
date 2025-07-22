from fastapi import APIRouter
from sqlmodel import select, desc
from app.models import Collection

from app.database import SessionDep
from app.schemas import UserCollectionsResponseSchema, CollectionSchema
from app.services.conversion_time import seconds_to_hms

router = APIRouter()

@router.get("/collections/{user_id}", response_model=UserCollectionsResponseSchema)
async def get_user_collections(
        session: SessionDep,
        user_id: str | None
):
    stmt = select(Collection).where(Collection.user_id==user_id).order_by(desc(Collection.created_at))
    result = await session.execute(stmt)
    collections_from_db  = result.scalars().all()

    collections_list = [
        CollectionSchema(
            title=collection.title,
            created_at=collection.created_at,
            duration=seconds_to_hms(collection.total_Listening_time)
        )
        for collection in collections_from_db
    ]

    return UserCollectionsResponseSchema(
        collections=collections_list
    )