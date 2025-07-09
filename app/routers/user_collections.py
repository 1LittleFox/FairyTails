from fastapi import APIRouter
from app.services import mock_data
from app.schemas import UserCollectionsResponseSchema

router = APIRouter()

@router.get("/user-collections", response_model=UserCollectionsResponseSchema)
async def get_user_collections():
    return mock_data.generate_mock_user_collections()