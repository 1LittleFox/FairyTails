import json
import os
import time

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from sqlmodel import select

from app.config import settings
from app.database import SessionDep
from app.models import User, Collection, Story
from app.schemas import Questionnaire, StoryGenerationResponse, UserAccessRequest
from app.services.audio_maker import YandexSpeechKitAudioMaker, GoogleCloudAudioMaker
from app.services.markup_prompt import create_markup_prompt_from_ru, create_markup_prompt_from_euro
from app.services.prompt_builder import prompt_user_builder

load_dotenv()
router = APIRouter()

OPENAI_API_KEY = settings.openai_api_key
OPENAI_MODEL = settings.openai_model
OPENAI_MODEL_FOR_MARKUP = settings.openai_model_for_markup


yandex_audio_maker = YandexSpeechKitAudioMaker()
google_audio_maker = GoogleCloudAudioMaker()


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

        print("Начали генерацию")
        start_time = time.time()
        try:
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)

            prompt = prompt_user_builder(data)

            print(prompt['user'])

            response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": f"{prompt['system']}. Всегда возвращай ответ в формате JSON."},
                    {"role": "user", "content": f"{prompt['user']}\n\nВерни ответ в формате JSON с полями: 'tale' (текст сказки), "
                                                f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}
                ],
                temperature=1,
                max_completion_tokens=16384
            )

            # Парсим JSON ответ
            tale_data = json.loads(response.choices[0].message.content)

            tale_text = tale_data['tale']

            tale_title = " ".join(tale_text.split()[:2]) + "..."

            if len(tale_text) < prompt['awg']:
                print("Начинаем увеличение сказки")
                start_time = time.time()
                expand_prompt = f"""
                    Расширь эту сказку до {prompt['awg']} символов.
                    Добавь смысловой нагрузки и связанных со сказкой деталей:

                    {tale_text}
                    """

                response = await client.chat.completions.create(
                    model=OPENAI_MODEL,
                    response_format={"type": "json_object"},
                    messages=[{"role": "user", "content": f"{expand_prompt}\n\nВерни ответ в формате JSON с полями: 'tale' (текст сказки), "
                                                f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}],
                    temperature=1,
                    max_completion_tokens=16384
                )

                if not response.choices[0].message.content:
                    raise ValueError("Пустой ответ от OpenAI")

                tale_data = json.loads(response.choices[0].message.content)
                tale_text = tale_data['tale']

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка генерации сказки: {str(e)}"
            )

        elapsed = time.time() - start_time
        print(f"Сказка написана: {elapsed:.1f} сек, приступаем к озвучке")

        characters_tale = len(tale_text)
        print(f"Длина сказки: {characters_tale}")

        print(f"Приступаем к разметке")
        start_time = time.time()
        if data.language == "РУС":
            try:
                client = AsyncOpenAI(api_key=OPENAI_API_KEY)

                markup_prompt = create_markup_prompt_from_ru(tale_text)

                response = await client.chat.completions.create(
                    model=OPENAI_MODEL,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": f"{markup_prompt['system_prompt_markup']}. Всегда возвращай ответ в формате JSON."},
                        {"role": "user",
                         "content": f"{markup_prompt['user_prompt_markup']}\n\nВерни ответ в формате JSON с полями: 'markup_tale' (текст сказки), "
                                    f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}
                    ],
                    temperature=1
                )

                # Парсим JSON ответ
                markup_tale_data = json.loads(response.choices[0].message.content)

                markup_tale_text = markup_tale_data['markup_tale']

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка разметки сказки: {str(e)}"
                )
            elapsed = time.time() - start_time
            print(f"Разметка выполнена успешно: {elapsed:.1f} сек")

            start_time = time.time()
            try:

                audio_url = await yandex_audio_maker.make_story_audio(markup_tale_text)

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка озвучивания сказки: {str(e)}"
                )

            elapsed = time.time() - start_time
            print(f"Озвучка выполнена успешно: {elapsed:.1f} сек")

        else:
            print(f"Приступаем к разметке для GC")
            start_time = time.time()
            try:
                client = AsyncOpenAI(api_key=OPENAI_API_KEY)

                markup_prompt = create_markup_prompt_from_euro(tale_text)

                response = await client.chat.completions.create(
                    model=OPENAI_MODEL_FOR_MARKUP,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": f"{markup_prompt['system_prompt_markup']}. Always return a response in JSON format."},
                        {"role": "user",
                         "content": f"{markup_prompt['user_prompt_markup']}\n\nReturn the response in JSON format with the fields: 'markup_tale' (text of the fairy tale), "
                                    f"'word_count' (number of words), 'target_words_usage' (dictionary of the use of target words)."}
                    ],
                    temperature=1
                )

                # Парсим JSON ответ
                markup_tale_data = json.loads(response.choices[0].message.content)

                markup_tale_text = markup_tale_data['markup_tale']

                markup_tale_text = str(markup_tale_text)

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка разметки сказки: {str(e)}"
                )
            elapsed = time.time() - start_time
            print(f"Разметка выполнена успешно: {elapsed:.1f} сек")

            if data.language == "FRA":
                voice_name = "fr-FR-Studio-A"
                language_code = "fr-FR"
                print(f"Начинаем озвучку")
                start_time = time.time()
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
                elapsed = time.time() - start_time
                print(f"Озвучка завершена: {elapsed:.1f} сек")
            else:
                voice_name = "en-US-Studio-O"
                language_code = "en-US"
                print(f"Начинаем озвучку")
                start_time = time.time()
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
                elapsed = time.time() - start_time
                print(f"Озвучка завершена: {elapsed:.1f} сек")


        new_collection = Collection(
            user_id=user_id,
            title=f"{tale_title}",
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
            title=new_story.title,
            content=new_story.content_story,
            url=new_story.audio_url
        )

    else:
        # User ID doesn't exist - return error or create new user with that ID
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {request.user_id} not found"
        )