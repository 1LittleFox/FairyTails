import os
import asyncio
from google.cloud import texttospeech
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()


async def test_google_cloud_tts():
    """Тест Google Cloud TTS для русского языка"""
    print("🎵 Тестируем Google Cloud TTS...")
    sempl_text = {'text':
    """Жил-был щенок по имени Дружок. 
    Он был очень любопытным и любил приключения. 
    Однажды, гуляя по лесу, Дружок встретил зайчонка Прыга и белочку Белянку."""}

    try:
        # Проверяем наличие учетных данных
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("❌ GOOGLE_APPLICATION_CREDENTIALS не установлен в .env")

        if not os.path.exists(credentials_path):
            raise ValueError(f"❌ Файл учетных данных не найден: {credentials_path}")

        print(f"✅ Учетные данные найдены: {credentials_path}")

        # Создаем клиент Google TTS
        client = texttospeech.TextToSpeechClient()

        print(f"📝 Озвучиваем текст: '{sempl_text[:50]}...'")

        # Настраиваем параметры синтеза
        synthesis_input = texttospeech.SynthesisInput(text=sempl_text)

        # Выбираем русский голос
        # Доступные русские голоса: ru-RU-Standard-A, ru-RU-Standard-B, ru-RU-Standard-C, ru-RU-Standard-D
        voice = texttospeech.VoiceSelectionParams(
            language_code="ru-RU",
            name="ru-RU-Standard-A",  # Женский голос
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        # Настройки аудио
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,  # Скорость речи (0.25 - 4.0)
            pitch=0.0,  # Высота тона (-20.0 - 20.0)
            volume_gain_db=0.0  # Громкость (-96.0 - 16.0)
        )

        print("🔄 Генерируем аудио...")

        # Выполняем синтез (синхронный вызов, но обернутый в async функцию)
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            client.synthesize_speech,
            {
                "input": synthesis_input,
                "voice": voice,
                "audio_config": audio_config
            }
        )

        # Сохраняем аудио файл
        output_filename = "test_google_tts_ru.mp3"
        with open(output_filename, "wb") as f:
            f.write(response.audio_content)

        print(f"✅ Google Cloud TTS работает! Создан файл: {output_filename}")
        print(f"📊 Размер файла: {len(response.audio_content)} байт")
        print(f"🎭 Использован голос: ru-RU-Standard-A (женский)")

        return True

    except Exception as e:
        print(f"❌ Ошибка Google Cloud TTS: {e}")
        return False

if __name__ == "__main__":
    # Запускаем основной тест
    asyncio.run(test_google_cloud_tts())

    # # Опционально: тест разных голосов
    # print("\n" + "=" * 50)
    # asyncio.run(test_multiple_voices())