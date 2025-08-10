import uuid

from fastapi import status, APIRouter, HTTPException
from sqlmodel import select

from app.schemas import CollectionDeleteResponse
from app.database import SessionDep
from app.models import Story, Collection

router = APIRouter()


@router.delete("/collection/{collection_id}", response_model=CollectionDeleteResponse)
async def delete_collection(
        collection_id: uuid.UUID,
        session: SessionDep
):
    """
    Удалить коллекцию и все связанные с ней сказки.
    Требует query параметр user_id с UUID пользователя
    """
    # Ищем коллекцию
    collection_statement = select(Collection).where(
        Collection.id == collection_id
    )
    collection_result = await session.execute(collection_statement)
    collection_to_delete = collection_result.scalars().first()

    if not collection_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection with ID {collection_id} not found or doesn't belong to user"
        )

    try:
        # Находим все сказки в коллекции для подсчета
        stories_statement = select(Story).where(Story.collection_id == collection_id)
        stories_result = await session.execute(stories_statement)
        stories_to_delete = stories_result.scalars().all()

        stories_count = len(stories_to_delete)

        # Удаляем все сказки в коллекции
        for story in stories_to_delete:
            await session.delete(story)

        # Удаляем саму коллекцию
        await session.delete(collection_to_delete)
        await session.commit()

        return CollectionDeleteResponse(
            message="Collection and all associated stories successfully deleted",
            deleted_collection_id=collection_id,
            deleted_stories_count=stories_count
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting collection: {str(e)}"
        )
