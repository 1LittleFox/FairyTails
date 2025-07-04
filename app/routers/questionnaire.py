from fastapi import APIRouter, status, HTTPException
from app.schemas import Questionnaire
from app.services.prompt_builder import prompt_builder

router = APIRouter()

@router.post("/questionnaire", status_code=status.HTTP_201_CREATED)
async def submit_questionnaire(data: Questionnaire):
    try:
        chatgpt_prompt = prompt_builder(data)

        return {
            "status": "success",
            "message": "Данные приняты, сказка формируется",
            "prompt_preview": chatgpt_prompt[:500] + "..."  # Сокращенный превью
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки: {str(e)}"

        )