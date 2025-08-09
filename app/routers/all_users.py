from fastapi import APIRouter
from sqlmodel import select
from app.database import SessionDep
from app.models import User

router = APIRouter()

@router.get("/all_users")
async def get_all_users(
        session: SessionDep,
):
    stmt = select(User).limit(50)
    result = await session.execute(stmt)
    home_collections = result.scalars().all()

    return home_collections