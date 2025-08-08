import os
import asyncio
import aiohttp
import socket
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

sample_text = """Здравствуйте, это тест голоса для T T S от Яндекс"""


def check_basic_connectivity():
    """Базовая проверка сетевого подключения"""
    print("🌐 Проверяем сетевое подключение...")

    # Проверяем общее подключение к интернету
    try:
        response = os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1")  # Linux/Mac
        if response != 0:
            response = os.system("ping -n 1 8.8.8.8 > nul 2>&1")  # Windows

        if response == 0:
            print("✅ Интернет подключение работает")
        else:
            print("❌ Нет подключения к интернету")
            return False
    except:
        print("⚠️ Не удалось проверить подключение к интернету")

    # Проверяем доступность Yandex API через альтернативные методы
    yandex_hosts = [
        'tts.api.cloud.yandex.net',
        'cloud.yandex.ru',
        'yandex.ru'
    ]

    for host in yandex_hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"✅ DNS работает: {host} -> {ip}")
            return True
        except socket.gaierror:
            print(f"❌ DNS не работает для: {host}")
            continue

    return False


async def simple_yandex_tts_test():
    """Простой тест Yandex SpeechKit TTS"""
    print("🎵 Простой тест Yandex SpeechKit TTS...")

    # Проверяем учетные данные
    api_key = os.getenv("YANDEX_API_KEY")
    folder_id = os.getenv("YANDEX_FOLDER_ID")

    if not api_key:
        print("❌ YANDEX_API_KEY не найден в .env файле")
        print("💡 Добавьте в .env: YANDEX_API_KEY=ваш_ключ")
        return False

    if not folder_id:
        print("❌ YANDEX_FOLDER_ID не найден в .env файле")
        print("💡 Добавьте в .env: YANDEX_FOLDER_ID=ваш_folder_id")
        return False

    print(f"✅ API ключ: {api_key[:10]}...")
    print(f"✅ Folder ID: {folder_id}")
    print(f"📝 Текст: '{sample_text}'")

    # Настройки запроса
    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

    headers = {
        'Authorization': f'Api-Key {api_key}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'text': sample_text,
        'lang': 'ru-RU',
        'voice': 'omazh',
        'emotion': 'neutral',
        'speed': 1.0,
        'format': 'mp3',
        'sampleRateHertz': 48000,
        'folderId': folder_id
    }

    print("🔄 Отправляем запрос к Yandex TTS...")

    # Настройки для обхода возможных блокировок
    timeout = aiohttp.ClientTimeout(total=60, connect=30)

    # Пробуем разные настройки подключения
    connector_configs = [
        # Стандартное подключение
        {"ttl_dns_cache": 300, "use_dns_cache": True},
        # Без DNS кеша
        {"ttl_dns_cache": 0, "use_dns_cache": False},
        # С увеличенными лимитами
        {"limit": 100, "ttl_dns_cache": 300}
    ]

    for i, config in enumerate(connector_configs):
        print(f"\n🔧 Попытка #{i + 1}: {config}")

        try:
            connector = aiohttp.TCPConnector(**config)

            async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
            ) as session:

                async with session.post(
                        url,
                        headers=headers,
                        data=data
                ) as response:

                    print(f"📡 Статус ответа: {response.status}")

                    if response.status == 200:
                        print("✅ Запрос успешен! Сохраняем аудио...")

                        audio_content = await response.read()
                        output_filename = "yandex_tts_test_omazh.mp3"

                        with open(output_filename, "wb") as f:
                            f.write(audio_content)

                        file_size = len(audio_content)
                        print(f"✅ УСПЕХ! Файл создан: {output_filename}")
                        print(f"📊 Размер: {file_size} байт ({file_size / 1024:.1f} KB)")
                        print(f"🎭 Голос: omazh")
                        return True

                    else:
                        error_text = await response.text()
                        print(f"❌ Ошибка API: {response.status}")
                        print(f"📄 Ответ: {error_text}")

                        # Диагностика ошибок
                        if response.status == 401:
                            print("💡 Проверьте правильность API ключа")
                        elif response.status == 400:
                            print("💡 Проверьте folder_id и параметры запроса")
                        elif response.status == 403:
                            print("💡 Нет прав на использование SpeechKit")

                        return False

        except aiohttp.ClientConnectorError as e:
            print(f"❌ Ошибка подключения #{i + 1}: {e}")
            if i < len(connector_configs) - 1:
                print("⏳ Пробуем другие настройки...")
                await asyncio.sleep(2)
            continue

        except asyncio.TimeoutError:
            print(f"❌ Таймаут #{i + 1}")
            if i < len(connector_configs) - 1:
                print("⏳ Пробуем с другими настройками...")
                await asyncio.sleep(2)
            continue

        except Exception as e:
            print(f"❌ Неожиданная ошибка #{i + 1}: {e}")
            if i < len(connector_configs) - 1:
                print("⏳ Пробуем еще раз...")
                await asyncio.sleep(2)
            continue

    print("\n❌ Все попытки подключения неудачны")
    print("\n🔧 Возможные решения:")
    print("1. Проверьте, не блокируется ли доступ к *.yandex.net")
    print("2. Попробуйте использовать VPN")
    print("3. Проверьте корпоративный файервол")
    print("4. Убедитесь что API ключ и folder_id корректны")

    return False


if __name__ == "__main__":
    print("🚀 Простой тест Yandex SpeechKit TTS")
    print("=" * 50)

    # Базовая проверка сети
    if not check_basic_connectivity():
        print("❌ Проблемы с базовым подключением к сети")
        print("💡 Проверьте интернет соединение")
        exit(1)

    # Основной тест
    success = asyncio.run(simple_yandex_tts_test())

    if success:
        print("\n🎉 Тест успешно завершен!")
        print("📁 Найдите файл yandex_tts_test.mp3 в текущей папке")
    else:
        print("\n❌ Тест не удался")
        print("💬 Свяжитесь с администратором сети или попробуйте VPN")