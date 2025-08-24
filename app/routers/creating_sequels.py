import json
import os
import time
from datetime import datetime, UTC

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from sqlalchemy import func
from sqlmodel import select

from app.database import SessionDep
from app.services.prompt_continue import prompt_continue_builder
from app.schemas import FollowUpQuestionnaire, StoryGenerationResponse
from app.models import Story, Collection
from app.routers.generation import google_audio_maker, yandex_audio_maker
from app.services.markup_prompt import create_markup_prompt_from_ru, create_markup_prompt_from_euro

load_dotenv()
router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-5"
OPENAI_MODEL_FOR_MARKUP = "gpt-4o"


@router.post("/stories/{story_id}/make_continue")
async def make_continue_for_story(
        session: SessionDep,
        story_id: str,
        data: FollowUpQuestionnaire
):
    start_time = time.time()

    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)

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
                {"role": "system", "content": f"{prompt_for_continuation['system']}. Всегда возвращай ответ в формате JSON."},
                {"role": "user",
                 "content": f"{prompt_for_continuation['user']}\n\nВерни ответ в формате JSON с полями: 'tale' (текст сказки), "
                                                f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}
            ],
            temperature=1,
            max_completion_tokens=16384
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

    if basis_for_continuation.language == "РУС":
        try:
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)

            markup_prompt = create_markup_prompt_from_ru(tale_text)

            response = await client.chat.completions.create(
                model=OPENAI_MODEL_FOR_MARKUP,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system",
                     "content": f"{markup_prompt['system_prompt_markup']}. Всегда возвращай ответ в формате JSON."},
                    {"role": "user",
                     "content": f"{markup_prompt['user_prompt_markup']}\n\nВерни ответ в формате JSON с полями: 'markup_tale' (текст сказки), "
                                f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}
                ],
                temperature=1,
                max_completion_tokens=16384
            )

            # Парсим JSON ответ
            markup_tale_data = json.loads(response.choices[0].message.content)

            markup_tale_text = markup_tale_data['markup_tale']

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка разметки сказки: {str(e)}"
            )

        try:
            audio_url = await yandex_audio_maker.make_story_audio(markup_tale_text)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка озвучивания сказки: {str(e)}"
            )

    else:
        try:
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            markup_prompt = create_markup_prompt_from_euro(tale_text)
            response = await client.chat.completions.create(
                model=OPENAI_MODEL_FOR_MARKUP,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system",
                     "content": f"{markup_prompt['system_prompt_markup']}. Always return a response in JSON format.."},
                    {"role": "user",
                     "content": f"{markup_prompt['user_prompt_markup']}\n\nReturn the response in JSON format with the fields: 'markup_tale' (text of the fairy tale), "
                                f"'word_count' (number of words), 'target_words_usage' (dictionary of the use of target words)."}
                ],
                temperature=0.9
            )

            # Парсим JSON ответ

            markup_tale_data = json.loads(response.choices[0].message.content)
            markup_tale_text = markup_tale_data['markup_tale']


        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка разметки сказки: {str(e)}"
            )

        if basis_for_continuation.language == "FRA":
            voice_name = "fr-FR-Studio-A"
            language_code = "fr-FR"

            try:

                audio_url = await google_audio_maker.make_story_audio(
                    story_text=markup_tale_text,
                    voice_name=voice_name,
                    language_code=language_code
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка озвучивания сказки: {str(e)}"
                )

        else:
            voice_name = "en-US-Studio-O"
            language_code = "en-US"

            try:

                audio_url = await google_audio_maker.make_story_audio(
                    story_text=markup_tale_text,
                    voice_name=voice_name,
                    language_code=language_code
                )

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
        audio_url=audio_url["url"],
        duration_seconds=audio_url["duration"],
        age_in_months=new_age,
        ethnography=basis_for_continuation.ethnography,
        interests=basis_for_continuation.interests,
        language=basis_for_continuation.language,
        gender=basis_for_continuation.gender
    )

    session.add(new_story)
    await session.commit()
    await session.refresh(new_story)

    # Получаем коллекцию
    collection_statement = select(Collection).where(Collection.id == basis_for_continuation.collection_id)
    collection_result = await session.execute(collection_statement)
    collection = collection_result.scalars().first()

    if not collection:
        raise ValueError(f"Collection with ID {basis_for_continuation.collection_id} not found")

    # Вычисляем сумму времени всех сказок в коллекции
    total_time_statement = select(func.coalesce(func.sum(Story.duration_seconds), 0)).where(
        Story.collection_id == basis_for_continuation.collection_id
    )
    total_time_result = await session.execute(total_time_statement)
    total_listening_time = total_time_result.scalar()

    # Обновляем коллекцию
    collection.total_Listening_time = total_listening_time

    await session.commit()
    await session.refresh(collection)

    elapsed = time.time() - start_time
    print(f"Конец ендпоинта. Время создания: {elapsed} сек")

    return StoryGenerationResponse(
        user_id=basis_for_continuation.user_id,
        created_at=new_story.created_at,
        title=new_story.title,
        content=new_story.content_story,
        url=new_story.audio_url
    )