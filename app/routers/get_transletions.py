from fastapi import APIRouter
from app.localization.utils import get_translation

router = APIRouter()

@router.get("/api/translations/{locale}")
async def get_translations(locale: str):
    return get_translation(locale)