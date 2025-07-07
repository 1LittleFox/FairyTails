from pathlib import Path
import uuid
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse
from openai import AsyncOpenAI
from app.config import config

router = APIRouter()
OPENAI_MODEL = "tts-1-hd"
MAX_TEXT_LENGTH = 4096

@router.post("/generate-voiceover")
async def generate_voiceover(tale: str = Body(..., embed=True)):
    try:
        if len(tale) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Текст превышает лимит в {MAX_TEXT_LENGTH} символов"
            )

        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY.get_secret_value())
        speech_file = f"speech_{uuid.uuid4().hex}.mp3"
        speech_file_path = Path(__file__).parent / speech_file

        response = await client.audio.speech.create(
          model=OPENAI_MODEL,
          voice="alloy",
          input=tale
        )

        await response.write_to_file(speech_file_path)

        return FileResponse(
          path=speech_file_path,
          media_type="audio/mpeg",
          filename=speech_file
        )

    except Exception as e:
      raise HTTPException(
        status_code=500,
        detail=f"Ошибка генерации озвучки: {str(e)}"
      )
