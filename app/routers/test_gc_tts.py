import os
import asyncio
from google.cloud import texttospeech
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

sempl_text = """
     <speak> <p> <s>In a little village nestled between whispering birch forests and fields of golden wheat, lived a quiet boy named Misha.</s> <break time="300ms"/> <s>His cottage had a thatched roof that wore a crown of moss, and his best friend was a fluffy ginger cat named Zhivchik, which means "lively one."</s> <break time="400ms"/> <s>Every evening, Misha's grandmother would stoke the warm, crackling fire in their big clay stove, and the whole house would glow with a cozy light.</s> <break time="500ms"/> <s>Zhivchik would curl his tail neatly around his paws and watch the dancing flames, his eyes two little moons in the firelight.</s> </p> <break time="600ms"/></speak>
"""


def check_network_connectivity():
    """Проверка сетевого подключения к Google APIs"""
    import socket
    import requests

    print("🌐 Проверяем сетевое подключение...")

    if len(sempl_text) > 5000:
        print("⚠️ Текст превышает лимит в 5000 символов!")
        print("💡 Рекомендуется разбить на части или сократить")
        return False
    # Проверка DNS разрешения
    try:
        ip = socket.gethostbyname('texttospeech.googleapis.com')
        print(f"✅ DNS разрешение успешно: texttospeech.googleapis.com -> {ip}")
    except socket.gaierror as e:
        print(f"❌ DNS ошибка: {e}")
        return False

    # Проверка HTTP подключения
    try:
        response = requests.get('https://texttospeech.googleapis.com', timeout=10)
        print(f"✅ HTTP подключение успешно: статус {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP ошибка: {e}")
        return False


async def test_google_cloud_tts():
    """Тест Google Cloud TTS для русского языка"""
    print("🎵 Тестируем Google Cloud TTS...")

    if not check_network_connectivity():
        print("❌ Проблемы с сетевым подключением. Проверьте интернет и DNS настройки.")
        return False

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
        synthesis_input = texttospeech.SynthesisInput(ssml=sempl_text)

        name="fr-FR-Studio-D"

        # Выбираем русский голос
        # Доступные русские голоса: ru-RU-Standard-A, ru-RU-Standard-B, ru-RU-Standard-C, ru-RU-Standard-D
        voice = texttospeech.VoiceSelectionParams(
            language_code="fr-FR",
            name=name,  # Женский голос
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )

        # Настройки аудио
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,  # Скорость речи (0.25 - 4.0)
            volume_gain_db=-2.0
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
        output_filename = f"google_tts_{name}_MALE.mp3"
        with open(output_filename, "wb") as f:
            f.write(response.audio_content)

        print(f"✅ Google Cloud TTS работает! Создан файл: {output_filename}")
        print(f"📊 Размер файла: {len(response.audio_content)} байт")
        print(f"🎭 Использован голос: {name}")

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