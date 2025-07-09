from fastapi import APIRouter
from app.services import mock_data
from app.schemas import CollectionsResponseSchema

router = APIRouter()

@router.get("/collections", response_model=CollectionsResponseSchema)
async def get_collections():
    return mock_data.generate_mock_collections()