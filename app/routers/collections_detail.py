from fastapi import APIRouter, HTTPException
from app.services import mock_data
from app.schemas import CollectionDetailsSchema
import uuid

router = APIRouter()


@router.get("/user-collections/{collection_id}", response_model=CollectionDetailsSchema)
async def get_collection_details(collection_id: str):
    try:
        # Преобразуем строку в UUID
        collection_uuid = uuid.UUID(collection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid collection ID format")

    return mock_data.generate_mock_collection_details(collection_uuid)