import os
import uuid
from datetime import datetime

import boto3
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


class SimpleAudioMaker:
    """Простой класс для создания аудио и загрузки в S3"""

    def __init__(self):

        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.selectel_domain=os.getenv("SELECTEL_DOMAIN")
        # Настраиваем Selectel S3
        self.s3_client = boto3.client(
            's3',
            endpoint_url='https://s3.ru-1.storage.selcloud.ru',
            aws_access_key_id=os.getenv("SELECTEL_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("SELECTEL_SECRET_KEY"),
            region_name='ru-1',
            config=boto3.session.Config(
                s3={'addressing_style': 'virtual'}
            )
        )

        self.bucket_name = os.getenv("SELECTEL_BUCKET_NAME")


    async def create_audio(self, text: str) -> bytes:
        """ШАГ 1: Создаем аудио из текста асинхронно"""

        response = await self.openai_client.audio.speech.create(
            model="tts-1-hd",  # Модель (можно tts-1-hd для лучшего качества)
            voice="alloy",  # Голос (alloy, echo, fable, onyx, nova, shimmer)
            input=text
        )

        audio_data = response.content

        return audio_data

    def upload_to_s3(self, audio_data: bytes) -> str:
        """ШАГ 2: Загружаем аудио в S3"""

        # Преобразуем user_id в строку (для UUID и обычных строк)

        # Создаем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"audio/{timestamp}_{unique_id}.mp3"

        # Загружаем в S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=filename,
            Body=audio_data,
            ContentType='audio/mpeg',
            ACL='public-read'
        )

        # Формируем URL (vHosted формат для вашего контейнера)
        file_url = f"{self.selectel_domain}/{filename}"

        return file_url

    async def make_story_audio(self, story_text: str) -> str:
        """ГЛАВНАЯ ФУНКЦИЯ: Текст → Аудио → S3 → URL"""

        try:
            # Шаг 1: Текст → Аудио (теперь асинхронно)
            audio_data = await self.create_audio(story_text)

            # Шаг 2: Аудио → S3
            audio_url = self.upload_to_s3(audio_data)

            return audio_url

        except Exception as e:
            raise Exception(f"Не удалось создать аудио: {e}")
