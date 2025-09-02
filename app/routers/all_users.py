from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import select
from app.database import SessionDep
from app.models import User
from app.auth_utils import verify_swagger_credentials

router = APIRouter()

@router.get("/all_users")
async def get_all_users(
        session: SessionDep,
        authenticated_admin: str = Depends(verify_swagger_credentials)
):
    stmt = select(User).limit(50)
    result = await session.execute(stmt)
    users = result.scalars().all()

    return {
        "users": users,
        "accessed_by": authenticated_admin,
        "access_time": datetime.now().isoformat()
    }