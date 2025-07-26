from fastapi import APIRouter
from sqlmodel import select

from app.database import SessionDep
from app.models import Story
from app.schemas import AudioStoryResponse

router = APIRouter()

@router.get("/users/{user_id}/stories/{story_id}/audio", response_model=AudioStoryResponse)
async def story_audio(
        session: SessionDep,
        story_id: str,
        user_id: str
):
    stmt = select(Story).where(Story.id == story_id)
    result = await session.execute(stmt)
    selected_story = result.scalars().first()

    return AudioStoryResponse(
        id=selected_story.id,
        title=selected_story.title,
        audio_url=selected_story.audio_url,
        text_content=selected_story.content_story
    )