import uuid

from fastapi import status, APIRouter, HTTPException
from sqlmodel import select

from app.schemas import DeleteResponse, UserAccessRequest
from app.database import SessionDep
from app.models import Story, Collection

router = APIRouter()

@router.delete("/story/{story_id}", response_model=DeleteResponse)
async def delete_story(
        story_id: uuid.UUID,
        session: SessionDep
):
    """
    Удалить конкретную сказку по ID
    """

    # Ищем сказку и проверяем принадлежность пользователю
    story_statement = select(Story).where(
        Story.id == story_id
    )
    story_result = await session.execute(story_statement)
    story_to_delete = story_result.scalars().first()

    if not story_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story with ID {story_id} not found or doesn't belong to user"
        )

    try:
        # Получаем коллекцию для обновления времени прослушивания
        collection_statement = select(Collection).where(
            Collection.id == story_to_delete.collection_id
        )
        collection_result = await session.execute(collection_statement)
        collection = collection_result.scalars().first()

        if collection:
            # Вычитаем время удаляемой сказки из общего времени коллекции
            collection.total_Listening_time = max(
                0,
                collection.total_Listening_time - story_to_delete.duration_seconds
            )

        # Удаляем сказку
        await session.delete(story_to_delete)
        await session.commit()

        return DeleteResponse(
            message="Story successfully deleted",
            deleted_id=story_id
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting story: {str(e)}"
        )