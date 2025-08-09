import os
import io
import uuid
import boto3
import aiohttp

from openai import AsyncOpenAI
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from google.cloud import texttospeech
from google.oauth2 import service_account
from mutagen.mp3 import MP3


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


    async def create_audio(self, text: str) -> tuple[bytes, float]:
        """ШАГ 1: Создаем аудио из текста асинхронно"""

        response = await self.openai_client.audio.speech.create(
            model="tts-1-hd",  # Модель (можно tts-1-hd для лучшего качества)
            voice="alloy",  # Голос (alloy, echo, fable, onyx, nova, shimmer)
            input=text
        )

        audio_data = response.content

        # Получаем длительность аудио
        try:
            audio_file = io.BytesIO(audio_data)
            audio = MP3(audio_file)
            duration = audio.info.length  # в секундах
        except Exception as e:
            print(f"Не удалось получить длительность аудио: {e}")
            duration = 0.0

        return audio_data, duration

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

    async def make_story_audio(self, story_text: str) -> dict:
        """ГЛАВНАЯ ФУНКЦИЯ: Текст → Аудио → S3 → URL"""

        try:
            # Шаг 1: Текст → Аудио (теперь асинхронно)
            audio_data, duration = await self.create_audio(story_text)

            # Шаг 2: Аудио → S3
            audio_url = self.upload_to_s3(audio_data)

            return {
                'url': audio_url,
                'duration': duration  # длительность в секундах
            }

        except Exception as e:
            raise Exception(f"Не удалось создать аудио: {e}")


class YandexSpeechKitAudioMaker:
    """Класс для создания аудио через Yandex SpeechKit и загрузки в S3"""

    def __init__(self):
        self.api_key = os.getenv("YANDEX_API_KEY")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")

        self.selectel_domain = os.getenv("SELECTEL_DOMAIN")

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

    async def create_audio(self, sample_text) -> tuple[bytes, float]:
        """ШАГ 1: Создаем аудио из текста через Yandex SpeechKit"""

        #
        data = {
            'ssml': sample_text,
            'lang': 'ru-RU',
            'voice': 'zahar',
            'emotion': 'neutral',
            'speed': 1.0,
            'format': 'mp3',
            'sampleRateHertz': 48000,
            'folderId': self.folder_id
        }

        url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Yandex SpeechKit API error {response.status}: {error_text}")

                audio_data = await response.read()

        # Получаем длительность аудио
        try:
            audio_file = io.BytesIO(audio_data)
            audio = MP3(audio_file)
            duration = audio.info.length  # в секундах
        except Exception as e:
            print(f"Не удалось получить длительность аудио: {e}")
            duration = 0.0

        return audio_data, duration

    def upload_to_s3(self, audio_data: bytes) -> str:
        """ШАГ 2: Загружаем аудио в S3"""

        # Создаем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"audio/yandex_tts_{timestamp}_{unique_id}.mp3"

        # Загружаем в S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=filename,
            Body=audio_data,
            ContentType='audio/mpeg',
            ACL='public-read'
        )

        # Формируем URL
        file_url = f"{self.selectel_domain}/{filename}"

        return file_url

    async def make_story_audio(self, story_text: str, voice: Optional[str] = None,
                               emotion: Optional[str] = None,
                               speed: Optional[float] = None,
                               lang: Optional[str] = None) -> dict:
        """ГЛАВНАЯ ФУНКЦИЯ: Текст → Аудио (Yandex SpeechKit) → S3 → URL"""

        try:
            # Шаг 1: Текст → Аудио через Yandex SpeechKit
            audio_data, duration = await self.create_audio(
                story_text,
                voice=voice,
                emotion=emotion,
                speed=speed,
                lang=lang
            )

            # Шаг 2: Аудио → S3
            audio_url = self.upload_to_s3(audio_data)

            return {
                'url': audio_url,
                'duration': duration,  # длительность в секундах
                'service': 'yandex_speechkit'
            }

        except Exception as e:
            raise Exception(f"Не удалось создать аудио через Yandex SpeechKit: {e}")


# class GoogleCloudAudioMaker:
#     """Класс для создания аудио через Google Cloud TTS и загрузки в S3"""
#
#     def __init__(self):
#         # Если ключ передан как путь к файлу
#         credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
#         self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
#
#         self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
#         self.client = texttospeech.TextToSpeechClient(credentials=self.credentials)
#
#         self.selectel_domain = os.getenv("SELECTEL_DOMAIN")
#
#         # Настраиваем Selectel S3
#         self.s3_client = boto3.client(
#             's3',
#             endpoint_url='https://s3.ru-1.storage.selcloud.ru',
#             aws_access_key_id=os.getenv("SELECTEL_ACCESS_KEY"),
#             aws_secret_access_key=os.getenv("SELECTEL_SECRET_KEY"),
#             region_name='ru-1',
#             config=boto3.session.Config(
#                 s3={'addressing_style': 'virtual'}
#             )
#         )
#
#         self.bucket_name = os.getenv("SELECTEL_BUCKET_NAME")
#
#     async def create_audio(self, text: str,
#                            voice_name: str,
#                            language_code: str) -> tuple[bytes, float]:
#         """ШАГ 1: Создаем аудио из текста через Google Cloud TTS"""
#
#         # Настройка входного текста
#         synthesis_input = texttospeech.SynthesisInput(text=text)
#
#         # Настройка голоса
#         voice = texttospeech.VoiceSelectionParams(
#             language_code=language_code,
#             name=voice_name
#         )
#
#         # Настройка аудио конфига
#         audio_config = texttospeech.AudioConfig(
#             audio_encoding=texttospeech.AudioEncoding.MP3,
#             speaking_rate=-0.9,
#             volume_gain_db=-2.0
#         )
#
#         # Выполняем синтез речи
#         response = self.client.synthesize_speech(
#             input=synthesis_input,
#             voice=voice,
#             audio_config=audio_config
#         )
#
#         audio_data = response.audio_content
#
#         # Получаем длительность аудио
#         try:
#             audio_file = io.BytesIO(audio_data)
#             audio = MP3(audio_file)
#             duration = audio.info.length  # в секундах
#         except Exception as e:
#             print(f"Не удалось получить длительность аудио: {e}")
#             duration = 0.0
#
#         return audio_data, duration
#
#     def upload_to_s3(self, audio_data: bytes) -> str:
#         """ШАГ 2: Загружаем аудио в S3"""
#
#         # Создаем уникальное имя файла
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         unique_id = str(uuid.uuid4())[:8]
#         filename = f"audio/gc_tts_{timestamp}_{unique_id}.mp3"
#
#         # Загружаем в S3
#         self.s3_client.put_object(
#             Bucket=self.bucket_name,
#             Key=filename,
#             Body=audio_data,
#             ContentType='audio/mpeg',
#             ACL='public-read'
#         )
#
#         # Формируем URL
#         file_url = f"{self.selectel_domain}/{filename}"
#
#         return file_url
#
#     async def make_story_audio(self, story_text: str,
#                            voice_name: str,
#                            language_code: str,
#                            speaking_rate: float) -> dict:
#         """ГЛАВНАЯ ФУНКЦИЯ: Текст → Аудио (GC TTS) → S3 → URL"""
#
#         try:
#             # Шаг 1: Текст → Аудио через Google Cloud TTS
#             audio_data, duration = await self.create_audio(
#                 story_text,
#                 voice_name=voice_name,
#                 language_code=language_code,
#                 speaking_rate=speaking_rate
#             )
#
#             # Шаг 2: Аудио → S3
#             audio_url = self.upload_to_s3(audio_data)
#
#             return {
#                 'url': audio_url,
#                 'duration': duration,  # длительность в секундах
#                 'service': 'google_cloud_tts'
#             }
#
#         except Exception as e:
#             raise Exception(f"Не удалось создать аудио через Google Cloud TTS: {e}")