import json
import os
from datetime import datetime, UTC

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from sqlmodel import select

from app.database import SessionDep
from app.services.prompt_builder import prompt_system_builder
from app.services.audio_maker import SimpleAudioMaker
from app.services.prompt_continue import prompt_continue_builder
from app.schemas import FollowUpQuestionnaire, StoryGenerationResponse
from app.models import Story, User





load_dotenv()
router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4-turbo"

audio_maker = SimpleAudioMaker()


@router.post("/users/{user_id}/stories/{story_id}/make_continue")
async def make_continue_for_story(
        session: SessionDep,
        story_id: str,
        user_id: str,
        data: FollowUpQuestionnaire
):
    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    existing_user = result.scalars().first()

    if existing_user:

        try:
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)

            system = prompt_system_builder()

            stmt = select(Story).where(Story.id == story_id)
            result = await session.execute(stmt)
            basis_for_continuation = result.scalars().first()

            story_created_at = basis_for_continuation.created_at
            continuation_created_at = datetime.now(UTC).replace(tzinfo=None)
            time_delta = continuation_created_at - story_created_at

            new_age = basis_for_continuation.age_in_months + time_delta.days // 30

            age_in_years = new_age // 12
            age_months = new_age % 12

            prompt_for_continuation = prompt_continue_builder(
                data=data,
                tale_text=basis_for_continuation.content_story,
                language=basis_for_continuation.language,
                gender=basis_for_continuation.gender,
                age_years=age_in_years,
                age_months=age_months,
                ethnography_choice=basis_for_continuation.ethnography,
                interest=basis_for_continuation.interests

            )

            response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": f"{system}. Всегда возвращай ответ в формате JSON."},
                    {"role": "user",
                     "content": f"{prompt_for_continuation}\n\nВерни ответ в формате JSON с полями: 'tale' (текст сказки), "
                                f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}
                ],
                temperature=0.3,
                max_tokens=3500,
                top_p=0.95,
                frequency_penalty=0.5,
                presence_penalty=0.3
            )

            # Парсим JSON ответ
            tale_data = json.loads(response.choices[0].message.content)

            tale_text = tale_data['tale']

            tale_title = " ".join(tale_text.split()[:2]) + "..."

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка генерации сказки: {str(e)}"
            )

        try:

            audio_url = await audio_maker.make_story_audio(tale_text)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка озвучивания сказки: {str(e)}"
            )

        new_story = Story(
            user_id=basis_for_continuation.user_id,
            collection_id=basis_for_continuation.collection_id,
            title=tale_title,
            content_story=tale_text,
            audio_url=audio_url,
            duration_seconds=data.story_duration_minutes * 60,
            age_in_months=new_age,
            ethnography_choice=basis_for_continuation.ethnography,
            interest=basis_for_continuation.interests,
            language=basis_for_continuation.language,
            gender=basis_for_continuation.gender
        )

        session.add(new_story)
        await session.commit()
        await session.refresh(new_story)

        return StoryGenerationResponse(
            user_id=basis_for_continuation.user_id,
            created_at=new_story.created_at,
            content=new_story.content_story,
            url=new_story.audio_url
        )



