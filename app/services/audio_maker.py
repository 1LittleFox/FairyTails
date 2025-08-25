import json
import os
import io
import re
import uuid

import boto3
import aiohttp
import wave

from datetime import datetime
from dotenv import load_dotenv
from google.cloud import texttospeech_v1 as texttospeech, storage
from google.oauth2 import service_account
from mutagen.mp3 import MP3

load_dotenv()

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

        self.max_chunk_size = 4500

    def remove_outer_speak_tags(self, ssml_text: str) -> str:
        """
        ШАГ 2: Удаляем внешние <speak> и </speak> теги
        """
        # Удаляем внешние speak теги, сохраняя все внутреннее содержимое
        ssml_text = ssml_text.strip()

        # Удаляем открывающий тег <speak> (может содержать атрибуты)
        ssml_text = re.sub(r'^\s*<speak>', '', ssml_text, flags=re.IGNORECASE)

        # Удаляем закрывающий тег </speak>
        ssml_text = re.sub(r'</speak>\s*$', '', ssml_text, flags=re.IGNORECASE)

        return ssml_text.strip()

    def split_by_p_tags(self, ssml_content: str) -> list[str]:
        """
        ШАГ 3: Разделяем контент на чанки по <p> тегам
        """
        chunks = []

        # Находим все <p>...</p> блоки
        p_pattern = r'<p[^>]*>.*?</p>'
        p_blocks = re.findall(p_pattern, ssml_content, re.DOTALL | re.IGNORECASE)

        if not p_blocks:
            # Если нет <p> тегов, возвращаем весь контент как один чанк
            print("Предупреждение: <p> теги не найдены, используется весь контент как один чанк")
            return [ssml_content]

        print(f"Найдено {len(p_blocks)} абзацев (<p> тегов)")

        current_chunk = ""

        for i, p_block in enumerate(p_blocks):
            # Проверяем, поместится ли текущий блок в чанк
            test_chunk = current_chunk + p_block
            test_chunk_with_speak = f"<speak>{test_chunk}</speak>"

            if len(test_chunk_with_speak) <= self.max_chunk_size:
                # Блок помещается, добавляем его к текущему чанку
                current_chunk = test_chunk
            else:
                # Блок не помещается
                if current_chunk:
                    # Сохраняем накопленный чанк
                    chunks.append(current_chunk)
                    current_chunk = p_block
                else:
                    # Текущий блок слишком большой даже сам по себе
                    print(f"Предупреждение: абзац {i + 1} слишком длинный ({len(p_block)} символов)")
                    # Можно добавить дополнительную логику разделения длинного абзаца
                    chunks.append(p_block)

        # Добавляем последний чанк, если он не пустой
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def add_speak_tags_to_chunks(self, chunks: list[str]) -> list[str]:
        """
        ШАГ 4: Добавляем <speak></speak> теги к каждому чанку

        Args:
            chunks: Список чанков без внешних speak тегов
        """
        wrapped_chunks = []

        for i, chunk in enumerate(chunks):
            # Формируем тег с атрибутами
            wrapped_chunk = f"<speak>{chunk}</speak>"
            wrapped_chunks.append(wrapped_chunk)

            print(f"Чанк {i + 1}: {len(wrapped_chunk)} символов")

        return wrapped_chunks

    async def create_audio_chunk(self, ssml_chunk) -> tuple[bytes, float]:
        """ШАГ 1: Создаем аудио из текста через Yandex SpeechKit"""

        #
        data = {
            'ssml': ssml_chunk,
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
            print(f"Не удалось получить длительность аудио чанка: {e}")
            duration = 0.0

        return audio_data, duration

    @staticmethod
    def concatenate_audio_files(audio_chunks: list[bytes]) -> bytes:
        """
        ШАГ 6: Соединяем аудио файлы
        """
        print(len(audio_chunks))
        if len(audio_chunks) == 1:
            return audio_chunks[0]

        return b''.join(audio_chunks)

    async def create_audio_from_ssml(self, ssml_text: str) -> tuple[bytes, float]:
        """
        ОСНОВНОЙ МЕТОД: Реализация вашего алгоритма
        1. Разметка уже есть (ssml_text)
        2. Удаляем внешние <speak></speak>
        3. Разделяем по <p> тегам
        4. Добавляем <speak></speak> к каждому чанку
        5. Озвучиваем каждый чанк
        6. Соединяем результаты
        """
        print(f"Начинаем обработку SSML текста длиной {len(ssml_text)} символов")

        # ШАГ 2: Удаляем внешние <speak></speak> теги
        content_without_speak = self.remove_outer_speak_tags(ssml_text)
        print(f"Контент без внешних speak тегов: {len(content_without_speak)} символов")

        # ШАГ 3: Разделяем на чанки по <p> тегам
        chunks = self.split_by_p_tags(content_without_speak)
        print(f"Получено чанков: {len(chunks)}")

        # Если все помещается в один чанк, используем исходный SSML
        if len(chunks) == 1 and len(ssml_text) <= self.max_chunk_size:
            print("Текст помещается в один чанк, используем как есть")
            return await self.create_audio_chunk(ssml_text)

        # ШАГ 4: Добавляем <speak></speak> к каждому чанку
        wrapped_chunks = self.add_speak_tags_to_chunks(chunks)

        # ШАГ 5: Озвучиваем каждый чанк
        audio_chunks = []
        total_duration = 0.0

        for i, chunk in enumerate(wrapped_chunks):
            try:
                print(f"Озвучиваем чанк {i + 1}/{len(wrapped_chunks)}")
                audio_data, duration = await self.create_audio_chunk(chunk)
                audio_chunks.append(audio_data)
                total_duration += duration
                print(f"  Длительность чанка: {duration:.2f} секунд")

            except Exception as e:
                raise Exception(f"Ошибка при озвучке чанка {i + 1}: {e}")

        # ШАГ 6: Соединяем аудио
        print("Соединяем аудио чанки...")
        combined_audio = self.concatenate_audio_files(audio_chunks)

        print(f"Общая длительность: {total_duration:.2f} секунд")
        return combined_audio, total_duration

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

    async def make_story_audio(self, story_text: str) -> dict:
        """ГЛАВНАЯ ФУНКЦИЯ: Текст → Аудио (Yandex SpeechKit) → S3 → URL"""

        try:
            # Шаг 1: Текст → Аудио через Yandex SpeechKit
            audio_data, duration = await self.create_audio_from_ssml(
                story_text
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


class GoogleCloudAudioMaker:
    """Класс для создания длинных аудио через Google Cloud TTS и загрузки в S3"""

    def __init__(self):
        credentials_json = os.getenv("GOOGLE_CLOUD_CREDENTIALS")
        if not credentials_json:
            raise ValueError("GOOGLE_CLOUD_CREDENTIALS environment variable not found")

        # Парсим JSON и создаем credentials объект
        credentials_dict = json.loads(credentials_json)
        self.credentials = service_account.Credentials.from_service_account_info(credentials_dict)

        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

        # Инициализируем клиент для длинных аудио
        self.long_audio_client = texttospeech.TextToSpeechLongAudioSynthesizeClient(
            credentials=self.credentials
        )

        # Инициализируем клиент для Google Cloud Storage
        self.gcs_client = storage.Client(credentials=self.credentials, project=self.project_id)

        # Настройки для временного GCS bucket (должен существовать)
        self.temp_gcs_bucket = os.getenv("TEMP_GCS_BUCKET_NAME")
        if not self.temp_gcs_bucket:
            raise ValueError("TEMP_GCS_BUCKET_NAME environment variable not found")

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

        self.max_chunk_size = 3500

    def remove_outer_speak_tags(self, ssml_text: str) -> str:
        """
        ШАГ 2: Удаляем внешние <speak> и </speak> теги
        """
        # Удаляем внешние speak теги, сохраняя все внутреннее содержимое
        ssml_text = ssml_text.strip()

        # Удаляем открывающий тег <speak> (может содержать атрибуты)
        ssml_text = re.sub(r'^\s*<speak>', '', ssml_text, flags=re.IGNORECASE)

        # Удаляем закрывающий тег </speak>
        ssml_text = re.sub(r'</speak>\s*$', '', ssml_text, flags=re.IGNORECASE)

        return ssml_text.strip()

    def split_by_p_tags(self, ssml_content: str) -> list[str]:
        """
        ШАГ 3: Разделяем контент на чанки по <p> тегам
        """
        chunks = []

        # Находим все <p>...</p> блоки
        p_pattern = r'<p[^>]*>.*?</p>'
        p_blocks = re.findall(p_pattern, ssml_content, re.DOTALL | re.IGNORECASE)

        if not p_blocks:
            # Если нет <p> тегов, возвращаем весь контент как один чанк
            print("Предупреждение: <p> теги не найдены, используется весь контент как один чанк")
            return [ssml_content]

        print(f"Найдено {len(p_blocks)} абзацев (<p> тегов)")

        current_chunk = ""

        for i, p_block in enumerate(p_blocks):
            # Проверяем, поместится ли текущий блок в чанк
            test_chunk = current_chunk + p_block
            test_chunk_with_speak = f"<speak>{test_chunk}</speak>"

            if len(test_chunk_with_speak) <= self.max_chunk_size:
                # Блок помещается, добавляем его к текущему чанку
                current_chunk = test_chunk
            else:
                # Блок не помещается
                if current_chunk:
                    # Сохраняем накопленный чанк
                    chunks.append(current_chunk)
                    current_chunk = p_block
                else:
                    # Текущий блок слишком большой даже сам по себе
                    print(f"Предупреждение: абзац {i + 1} слишком длинный ({len(p_block)} символов)")
                    # Можно добавить дополнительную логику разделения длинного абзаца
                    chunks.append(p_block)

        # Добавляем последний чанк, если он не пустой
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def add_speak_tags_to_chunks(self, chunks: list[str]) -> list[str]:
        """
        ШАГ 4: Добавляем <speak></speak> теги к каждому чанку

        Args:
            chunks: Список чанков без внешних speak тегов
        """
        wrapped_chunks = []

        for i, chunk in enumerate(chunks):
            # Формируем тег с атрибутами
            wrapped_chunk = f"<speak>{chunk}</speak>"
            wrapped_chunks.append(wrapped_chunk)

            print(f"Чанк {i + 1}: {len(wrapped_chunk)} символов")

        return wrapped_chunks

    async def create_audio_chunk(self, text: str,
                                voice_name: str,
                                language_code: str) -> tuple[bytes, float]:
        """ШАГ 1: Создаем длинное аудио из текста через Google Cloud TTS Long Audio Synthesis"""

        # Создаем уникальное имя для временного файла в GCS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        temp_filename = f"temp_audio_{timestamp}_{unique_id}.wav"
        output_gcs_uri = f"gs://{self.temp_gcs_bucket}/{temp_filename}"

        # Настройка входного текста
        synthesis_input = texttospeech.SynthesisInput(ssml=text)

        # Настройка голоса
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        # Настройка аудио конфига
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=0.9,
            volume_gain_db=-2.0
        )

        # Создаем запрос для длинного аудио синтеза
        request = texttospeech.SynthesizeLongAudioRequest(
            parent=f"projects/{self.project_id}/locations/global",
            input=synthesis_input,
            audio_config=audio_config,
            voice=voice,
            output_gcs_uri=output_gcs_uri
        )

        # Запускаем операцию синтеза
        operation = self.long_audio_client.synthesize_long_audio(request=request)

        # Ждем завершения операции
        result = operation.result(timeout=1800)  # 30 минут timeout

        # Скачиваем файл из GCS
        bucket = self.gcs_client.bucket(self.temp_gcs_bucket, user_project=self.project_id)

        blob = bucket.blob(temp_filename)

        # Скачиваем аудио данные
        audio_data = blob.download_as_bytes()

        # Получаем длительность аудио
        try:
            audio_file = io.BytesIO(audio_data)
            with wave.open(audio_file, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
        except Exception as e:
            print(f"Не удалось получить длительность аудио: {e}")
            duration = 0.0

        # Удаляем временный файл из GCS
        try:
            blob.delete()
            print(f"Временный файл {temp_filename} удален из GCS")
        except Exception as e:
            print(f"Не удалось удалить временный файл из GCS: {e}")

        return audio_data, duration

    @staticmethod
    def concatenate_audio_files(audio_chunks: list[bytes]) -> bytes:
        """
        ШАГ 6: Соединяем аудио файлы
        """
        print(len(audio_chunks))
        if len(audio_chunks) == 1:
            return audio_chunks[0]

        # Создаем выходной буфер
        output_buffer = io.BytesIO()

        # Открываем первый файл, чтобы получить параметры
        first_file = io.BytesIO(audio_chunks[0])
        with wave.open(first_file, 'rb') as first_wav:
            params = first_wav.getparams()

            # Создаем выходной WAV файл с теми же параметрами
            with wave.open(output_buffer, 'wb') as output_wav:
                output_wav.setparams(params)

                # Записываем данные из первого файла
                output_wav.writeframes(first_wav.readframes(first_wav.getnframes()))

                # Добавляем данные из остальных файлов
                for chunk in audio_chunks[1:]:
                    chunk_buffer = io.BytesIO(chunk)
                    with wave.open(chunk_buffer, 'rb') as chunk_wav:
                        # Просто добавляем аудио данные, игнорируя заголовки
                        output_wav.writeframes(chunk_wav.readframes(chunk_wav.getnframes()))

        # Возвращаем склеенный файл как bytes
        return output_buffer.getvalue()

    async def create_audio_from_ssml(self, ssml_text: str,
                                     voice_name: str,
                                     language_code: str) -> tuple[bytes, float]:
        """
        ОСНОВНОЙ МЕТОД: Реализация вашего алгоритма
        1. Разметка уже есть (ssml_text)
        2. Удаляем внешние <speak></speak>
        3. Разделяем по <p> тегам
        4. Добавляем <speak></speak> к каждому чанку
        5. Озвучиваем каждый чанк
        6. Соединяем результаты
        """
        print(f"Начинаем обработку SSML текста длиной {len(ssml_text)} символов")

        # ШАГ 2: Удаляем внешние <speak></speak> теги
        content_without_speak = self.remove_outer_speak_tags(ssml_text)
        print(f"Контент без внешних speak тегов: {len(content_without_speak)} символов")

        # ШАГ 3: Разделяем на чанки по <p> тегам
        chunks = self.split_by_p_tags(content_without_speak)
        print(f"Получено чанков: {len(chunks)}")

        # Если все помещается в один чанк, используем исходный SSML
        if len(chunks) == 1 and len(ssml_text) <= self.max_chunk_size:
            print("Текст помещается в один чанк, используем как есть")
            return await self.create_audio_chunk(ssml_text, voice_name, language_code)

        # ШАГ 4: Добавляем <speak></speak> к каждому чанку
        wrapped_chunks = self.add_speak_tags_to_chunks(chunks)

        # ШАГ 5: Озвучиваем каждый чанк
        audio_chunks = []
        total_duration = 0.0

        for i, chunk in enumerate(wrapped_chunks):
            try:
                print(f"Озвучиваем чанк {i + 1}/{len(wrapped_chunks)}")
                audio_data, duration = await self.create_audio_chunk(chunk, voice_name, language_code)
                audio_chunks.append(audio_data)
                total_duration += duration
                print(f"  Длительность чанка: {duration:.2f} секунд")

            except Exception as e:
                raise Exception(f"Ошибка при озвучке чанка {i + 1}: {e}")

        # ШАГ 6: Соединяем аудио
        print("Соединяем аудио чанки...")
        combined_audio = self.concatenate_audio_files(audio_chunks)

        print(f"Общая длительность: {total_duration:.2f} секунд")
        return combined_audio, total_duration

    def upload_to_s3(self, audio_data: bytes) -> str:
        """ШАГ 2: Загружаем аудио в S3"""

        # Создаем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"audio/gc_long_tts_{timestamp}_{unique_id}.wav"

        # Загружаем в S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=filename,
            Body=audio_data,
            ContentType='audio/wav',
            ACL='public-read'
        )

        # Формируем URL
        file_url = f"{self.selectel_domain}/{filename}"

        return file_url

    async def make_story_audio(self, story_text: str,
                               voice_name: str,
                               language_code: str) -> dict:
        """ГЛАВНАЯ ФУНКЦИЯ: Длинный текст → Аудио (GC Long TTS) → S3 → URL"""

        try:
            # Шаг 1: Длинный текст → Аудио через Google Cloud Long TTS
            audio_data, duration = await self.create_audio_from_ssml(
                story_text,
                voice_name=voice_name,
                language_code=language_code
            )

            # Шаг 2: Аудио → S3
            audio_url = self.upload_to_s3(audio_data)

            return {
                'url': audio_url,
                'duration': duration,  # длительность в секундах
                'service': 'google_cloud_long_tts'
            }

        except Exception as e:
            raise Exception(f"Не удалось создать длинное аудио через Google Cloud TTS: {e}")