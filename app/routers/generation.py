import json
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from sqlmodel import select

from app.database import SessionDep
from app.models import User, Collection, Story
from app.schemas import Questionnaire, StoryGenerationResponse, UserAccessRequest
from app.services.prompt_builder import prompt_user_builder
from app.services.audio_maker import SimpleAudioMaker
from app.services.markup_prompt import create_markup_prompt

load_dotenv()
router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4-turbo"

audio_maker = SimpleAudioMaker()

@router.post("/generation-tale", response_model=StoryGenerationResponse)
async def generate_tale_and_check_user(
        session: SessionDep,
        request: UserAccessRequest,
        data: Questionnaire
):
    user_id = request.user_id

    #Проверяем получал-ли пользователь свой uuid, если нет то создаем его
    if user_id is None:
        new_user = User()
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        user_id = new_user.id

    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    existing_user = result.scalars().first()

    if existing_user:

            try:
                client = AsyncOpenAI(api_key=OPENAI_API_KEY)

                prompt = prompt_user_builder(data)

                response = await client.chat.completions.create(
                    model=OPENAI_MODEL,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": f"{prompt["system"]}. Всегда возвращай ответ в формате JSON."},
                        {"role": "user", "content": f"{prompt["user"]}\n\nВерни ответ в формате JSON с полями: 'tale' (текст сказки), "
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
                client = AsyncOpenAI(api_key=OPENAI_API_KEY)

                markup_prompt = create_markup_prompt(tale_text)

                response = await client.chat.completions.create(
                    model=OPENAI_MODEL,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": f"{markup_prompt["system_prompt_markup"]}. Всегда возвращай ответ в формате JSON."},
                        {"role": "user",
                         "content": f"{markup_prompt["user_prompt_markup"]}\n\nВерни ответ в формате JSON с полями: 'markup_tale' (текст сказки), "
                                    f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}
                    ],
                    temperature=0.3
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

                audio_url = await audio_maker.make_story_audio(tale_text)

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка озвучивания сказки: {str(e)}"
                )


            new_collection = Collection(
                user_id=user_id,
                title=f"Stories about {tale_title}",
                total_Listening_time=audio_url["duration"]
            )

            session.add(new_collection)
            await session.commit()
            await session.refresh(new_collection)

            new_story = Story(
                user_id=user_id,
                collection_id=new_collection.id,
                title=tale_title,
                content_story=tale_text,
                audio_url=audio_url["url"],
                duration_seconds=audio_url["duration"],
                age_in_months=data.age_years*12 + data.age_months,
                ethnography=data.ethnography_choice,
                language=data.language,
                gender=data.gender,
                interests=data.subcategories
            )

            session.add(new_story)
            await session.commit()
            await session.refresh(new_story)

            return StoryGenerationResponse(
                user_id=user_id,
                created_at=new_story.created_at,
                content=new_story.content_story,
                url=new_story.audio_url
            )

    else:
        # User ID doesn't exist - return error or create new user with that ID
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {request.user_id} not found"
        )