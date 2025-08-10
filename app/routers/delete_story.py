import uuid

from fastapi import status, APIRouter, HTTPException
from sqlalchemy import func
from sqlmodel import select

from app.schemas import DeleteResponse
from app.database import SessionDep
from app.models import Story, Collection

router = APIRouter()

@router.delete("/storys/{story_id}", response_model=DeleteResponse)
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
        # Сохраняем collection_id перед удалением
        collection_id = story_to_delete.collection_id

        # Удаляем сказку
        await session.delete(story_to_delete)
        await session.commit()

        # Подсчитываем количество оставшихся сказок в коллекции одним запросом
        from sqlmodel import func
        remaining_count_statement = select(func.count(Story.id)).where(Story.collection_id == collection_id)
        remaining_count_result = await session.execute(remaining_count_statement)
        remaining_count = remaining_count_result.scalar()

        if remaining_count == 0:
            # Коллекция стала пустой - удаляем её
            collection_statement = select(Collection).where(Collection.id == collection_id)
            collection_result = await session.execute(collection_statement)
            empty_collection = collection_result.scalars().first()

            if empty_collection:
                await session.delete(empty_collection)
                await session.commit()

                return DeleteResponse(
                    message="Story deleted. Collection was empty and has been removed",
                    deleted_id=story_id
                )
        else:
            # Получаем коллекцию
            collection_statement = select(Collection).where(Collection.id == collection_id)
            collection_result = await session.execute(collection_statement)
            collection = collection_result.scalars().first()

            if not collection:
                raise ValueError(f"Collection with ID {collection_id} not found")

            # Вычисляем сумму времени всех сказок в коллекции
            total_time_statement = select(func.coalesce(func.sum(Story.duration_seconds), 0)).where(
                Story.collection_id == collection_id
            )
            total_time_result = await session.execute(total_time_statement)
            total_listening_time = total_time_result.scalar()

            # Обновляем коллекцию
            collection.total_Listening_time = total_listening_time

            await session.commit()
            await session.refresh(collection)

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