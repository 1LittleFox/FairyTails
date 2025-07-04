from click import prompt
from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel
from app.config import Config
import os

router = APIRouter()

OPENAI_MODEL = "gpt-3.5-turbo"  # Или "gpt-3.5-turbo" для экономии

@router.post("/generate-tales")
async def generate_tale():
    try:
        prompt = f"""Are you working?"""
        client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=50
        )

        tale_text = response.choices[0].message.content

        # TODO: Сохранение в БД (реализуем позже)
        # await save_to_db(tale_text, questionnaire)

        return {"tale": tale_text}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации сказки: {str(e)}"
        )