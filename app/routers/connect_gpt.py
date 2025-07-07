from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from app.config import config
from app.schemas import Questionnaire
from app.services.prompt_builder import prompt_system_builder, prompt_user_builder

router = APIRouter()

OPENAI_MODEL = "gpt-3.5-turbo"  # Или "gpt-3.5-turbo" для экономии

@router.post("/generate-tales")
async def generate_tale(data: Questionnaire):
    try:

        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY.get_secret_value())

        system = prompt_system_builder()
        prompt = prompt_user_builder(data)

        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=1.1,
            max_tokens=3500
        )

        tale_text = response.choices[0].message.content

        # TODO: Сохранение в БД (реализуем позже)
        # await save_to_db(tale_text, questionnaire)

        return {"system": system,
                "prompt": prompt,
                "tale": tale_text
                }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации сказки: {str(e)}"
        )