from fastapi import APIRouter
from sqlmodel import select
from app.database import SessionDep
from app.models import Collection

router = APIRouter()

@router.get("/all_collection")
async def get_all_collection(
        session: SessionDep,
):
    stmt = select(Collection)
    result = await session.execute(stmt)
    home_collections = result.scalars().all()

    return home_collections