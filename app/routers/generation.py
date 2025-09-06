import json
import os
import time
import uuid
from typing import Dict, Any

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


async def generate_tale_content(client: AsyncOpenAI, data: Questionnaire) -> Dict[str, Any]:
    """Генерация основного содержания сказки"""
    prompt = prompt_user_builder(data)

    print("Начали генерацию сказки")
    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": f"{prompt['system']}. Всегда возвращай ответ в формате JSON."},
            {"role": "user",
             "content": f"{prompt['user']}\n\nВерни ответ в формате JSON с полями: 'tale' (текст сказки), "
                        f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}
        ],
        temperature=1,
        max_completion_tokens=16384
    )

    tale_data = json.loads(response.choices[0].message.content)
    tale_text = tale_data['tale']

    answer = {
        "tale_text": tale_text,
        "awg": prompt['awg']
    }

    return answer


async def expand_tale_if_needed(client: AsyncOpenAI, tale_text: str, target_length: int) -> str:
    """Расширение сказки при необходимости"""
    print("Начинаем увеличение сказки")
    expand_prompt = f"""
        Расширь эту сказку до {target_length} символов.
        Добавь смысловой нагрузки и связанных со сказкой деталей:

        {tale_text}
        """

    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "user",
                   "content": f"{expand_prompt}\n\nВерни ответ в формате JSON с полями: 'tale' (текст сказки), "
                              f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}],
        temperature=1,
        max_completion_tokens=16384
    )

    expanded_data = json.loads(response.choices[0].message.content)
    return expanded_data['tale']


async def create_markup_russian(client: AsyncOpenAI, tale_text: str) -> str:
    """Создание разметки для русского текста"""
    print("Приступаем к разметке (РУС)")
    markup_prompt = create_markup_prompt_from_ru(tale_text)

    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system",
             "content": f"{markup_prompt['system_prompt_markup']}. Всегда возвращай ответ в формате JSON."},
            {"role": "user",
             "content": f"{markup_prompt['user_prompt_markup']}\n\nВерни ответ в формате JSON с полями: 'markup_tale' (текст сказки), "
                        f"'word_count' (количество слов), 'target_words_usage' (словарь использования целевых слов)."}
        ],
        temperature=1
    )

    markup_data = json.loads(response.choices[0].message.content)
    return markup_data['markup_tale']


async def create_markup_european(client: AsyncOpenAI, tale_text: str) -> str:
    """Создание разметки для европейских языков"""
    print("Приступаем к разметке (EUR)")
    markup_prompt = create_markup_prompt_from_euro(tale_text)

    response = await client.chat.completions.create(
        model=OPENAI_MODEL_FOR_MARKUP,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system",
             "content": f"{markup_prompt['system_prompt_markup']}. Always return a response in JSON format."},
            {"role": "user",
             "content": f"{markup_prompt['user_prompt_markup']}\n\nReturn the response in JSON format with the fields: 'markup_tale' (text of the fairy tale), "
                        f"'word_count' (number of words), 'target_words_usage' (dictionary of the use of target words)."}
        ],
        temperature=1
    )

    markup_data = json.loads(response.choices[0].message.content)
    return str(markup_data['markup_tale'])


async def create_audio_russian(markup_text: str) -> Dict[str, Any]:
    """Создание аудио для русского текста через Yandex"""
    print("Начинаем озвучку (Yandex)")
    return await yandex_audio_maker.make_story_audio(markup_text)


async def create_audio_european(markup_text: str, language: str) -> Dict[str, Any]:
    """Создание аудио для европейских языков через Google Cloud"""
    voice_config = {
        "FRA": {"voice_name": "fr-FR-Studio-A", "language_code": "fr-FR"},
        # По умолчанию английский для остальных языков
        "default": {"voice_name": "en-US-Studio-O", "language_code": "en-US"}
    }

    config = voice_config.get(language, voice_config["default"])
    print(f"Начинаем озвучку (Google Cloud - {language})")

    return await google_audio_maker.make_story_audio(
        story_text=markup_text,
        voice_name=config["voice_name"],
        language_code=config["language_code"]
    )


async def save_to_database(session: SessionDep, user_id: uuid.UUID, tale_title: str,
                           tale_text: str, audio_data: Dict[str, Any], data: Questionnaire) -> Story:
    """Сохранение данных в базу данных"""
    print("Сохраняем данные в БД")

    # Создание коллекции
    new_collection = Collection(
        user_id=user_id,
        title=tale_title,
        total_Listening_time=audio_data["duration"]
    )

    session.add(new_collection)
    await session.commit()
    await session.refresh(new_collection)

    # Создание истории
    new_story = Story(
        user_id=user_id,
        collection_id=new_collection.id,
        title=tale_title,
        content_story=tale_text,
        audio_url=audio_data["url"],
        duration_seconds=audio_data["duration"],
        age_in_months=data.age_years * 12 + data.age_months,
        ethnography=data.ethnography_choice,
        language=data.language,
        gender=data.gender,
        interests=data.subcategories
    )

    session.add(new_story)
    await session.commit()
    await session.refresh(new_story)

    return new_story


@router.post("/generation-tale", response_model=StoryGenerationResponse)
async def generate_tale_and_check_user(
        session: SessionDep,
        request: UserAccessRequest,
        data: Questionnaire
):
    start_total_time = time.time()
    user_id = request.user_id

    # Проверяем получал-ли пользователь свой uuid, если нет то создаем его
    if user_id is None:
        new_user = User()
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        user_id = new_user.id

    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    existing_user = result.scalars().first()

    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {request.user_id} not found"
        )

    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        # Этап 1: Генерация сказки (последовательно, так как зависят друг от друга)
        start_time = time.time()
        answer_after_generation = await generate_tale_content(client, data)
        tale_text = answer_after_generation['tale_text']

        # Расширение при необходимости
        if len(tale_text) <= answer_after_generation['awg']:
            tale_text = await expand_tale_if_needed(client, tale_text, answer_after_generation['awg'])

        tale_title = " ".join(tale_text.split()[:2]) + "..."
        print(f"Генерация сказки завершена: {time.time() - start_time:.1f} сек")
        print(f"Длина сказки: {len(tale_text)} символов")

        # Этап 2: Параллельная обработка разметки и подготовка к озвучке
        start_time = time.time()

        if data.language == "РУС":
            # Для русского: разметка → озвучка
            markup_text = await create_markup_russian(client, tale_text)
            print(f"Разметка выполнена: {time.time() - start_time:.1f} сек")

            start_audio_time = time.time()
            audio_data = await create_audio_russian(markup_text)
            print(f"Озвучка завершена: {time.time() - start_audio_time:.1f} сек")

        else:
            # Для европейских языков: разметка → озвучка
            markup_text = await create_markup_european(client, tale_text)
            print(f"Разметка выполнена: {time.time() - start_time:.1f} сек")

            start_audio_time = time.time()
            audio_data = await create_audio_european(markup_text, data.language)
            print(f"Озвучка завершена: {time.time() - start_audio_time:.1f} сек")

        # Этап 3: Сохранение в базу данных
        start_db_time = time.time()
        new_story = await save_to_database(session, user_id, tale_title, tale_text, audio_data, data)
        print(f"Сохранение в БД завершено: {time.time() - start_db_time:.1f} сек")

        print(f"Общее время выполнения: {time.time() - start_total_time:.1f} сек")

        return StoryGenerationResponse(
            user_id=user_id,
            created_at=new_story.created_at,
            title=new_story.title,
            content=new_story.content_story,
            url=new_story.audio_url
        )

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка парсинга JSON ответа: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации сказки: {str(e)}"
        )
