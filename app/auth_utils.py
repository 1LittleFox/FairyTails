# enhanced_auth_utils.py
import os
import secrets
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.config import settings

# Настройка специализированного логгера для аутентификации
auth_logger = logging.getLogger("authentication")
auth_logger.setLevel(logging.INFO)

# Определяем путь к папке логов относительно текущего файла
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # поднимаемся на уровень выше от app/
log_dir = os.path.join(project_root, 'logs')

# Создаем папку логов, если её нет
os.makedirs(log_dir, exist_ok=True)

# Создаем handler для записи в файл
auth_log_path = os.path.join(log_dir, 'auth.log')
auth_handler = logging.FileHandler(auth_log_path)
auth_formatter = logging.Formatter(
    '%(asctime)s - AUTH - %(levelname)s - %(message)s'
)
auth_handler.setFormatter(auth_formatter)
auth_logger.addHandler(auth_handler)

# Инициализируем HTTP Basic Authentication
security = HTTPBasic()


class AuthenticationManager:
    """
    Управляет аутентификацией с расширенными возможностями безопасности

    Функции:
    - Защита от брутфорс-атак
    - Подробное логирование
    - Временная блокировка IP-адресов
    - Контекстная информация о запросах
    """

    def __init__(self):
        # Отслеживание неудачных попыток по IP-адресам
        self.failed_attempts = defaultdict(lambda: deque())

        # Временно заблокированные IP-адреса
        self.blocked_ips = {}

        # Настройки безопасности
        self.max_attempts = 10  # Максимум попыток за временное окно
        self.time_window = 900  # 15 минут в секундах
        self.block_duration = 3600  # Блокировка на 1 час

    def _get_client_info(self, request: Request) -> dict:
        """Собирает информацию о клиенте для логирования"""
        return {
            "ip": self._get_real_ip(request),
            "user_agent": request.headers.get("user-agent", "Unknown"),
            "timestamp": datetime.now().isoformat(),
            "endpoint": str(request.url.path)
        }

    def _get_real_ip(self, request: Request) -> str:
        """Получает реальный IP-адрес с учетом прокси"""
        # Проверяем заголовки прокси (Nginx, CloudFlare и т.д.)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(',')[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host

    def _is_ip_blocked(self, ip: str) -> bool:
        """Проверяет, заблокирован ли IP-адрес"""
        if ip not in self.blocked_ips:
            return False

        # Проверяем, не истекла ли блокировка
        block_time = self.blocked_ips[ip]
        if datetime.now() > block_time:
            del self.blocked_ips[ip]
            return False

        return True

    def _record_failed_attempt(self, ip: str):
        """Записывает неудачную попытку и проверяет необходимость блокировки"""
        now = datetime.now()
        attempts = self.failed_attempts[ip]

        # Добавляем текущую попытку
        attempts.append(now)

        # Удаляем старые попытки вне временного окна
        cutoff_time = now - timedelta(seconds=self.time_window)
        while attempts and attempts[0] < cutoff_time:
            attempts.popleft()

        # Проверяем превышение лимита
        if len(attempts) >= self.max_attempts:
            # Блокируем IP
            self.blocked_ips[ip] = now + timedelta(seconds=self.block_duration)
            auth_logger.critical(
                f"IP {ip} blocked due to {len(attempts)} failed authentication attempts"
            )
            return True

        return False

    def authenticate_user(
            self,
            credentials: HTTPBasicCredentials,
            request: Request
    ) -> str:
        """
        Основная функция аутентификации с расширенными проверками безопасности

        Args:
            credentials: Учетные данные HTTP Basic Auth
            request: Объект запроса для получения контекстной информации

        Returns:
            str: Имя пользователя при успешной аутентификации

        Raises:
            HTTPException: При неверных данных или блокировке
        """
        client_info = self._get_client_info(request)
        client_ip = client_info["ip"]

        # Проверяем блокировку IP
        if self._is_ip_blocked(client_ip):
            auth_logger.warning(
                f"Blocked IP {client_ip} attempted authentication. "
                f"User-Agent: {client_info['user_agent']}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="IP address temporarily blocked due to multiple failed attempts",
                headers={"Retry-After": str(self.block_duration)}
            )

        # Получаем правильные учетные данные
        correct_username = settings.docs_username
        correct_password = settings.docs_password

        # Проверяем учетные данные (защита от timing-атак)
        username_correct = secrets.compare_digest(
            credentials.username.encode("utf-8"),
            correct_username.encode("utf-8")
        )
        password_correct = secrets.compare_digest(
            credentials.password.encode("utf-8"),
            correct_password.encode("utf-8")
        )

        authentication_successful = username_correct and password_correct

        if authentication_successful:
            # Успешная аутентификация
            auth_logger.info(
                f"Successful authentication: {credentials.username} from {client_ip}. "
                f"User-Agent: {client_info['user_agent']}"
            )

            # Очищаем неудачные попытки для этого IP
            if client_ip in self.failed_attempts:
                del self.failed_attempts[client_ip]

            return credentials.username

        else:
            # Неудачная попытка
            auth_logger.warning(
                f"Failed authentication attempt: username='{credentials.username}' "
                f"from {client_ip}. User-Agent: {client_info['user_agent']}"
            )

            # Записываем неудачную попытку
            self._record_failed_attempt(client_ip)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль",
                headers={"WWW-Authenticate": "Basic realm='Admin Access Required'"},
            )


# Создаем глобальный экземпляр менеджера аутентификации
auth_manager = AuthenticationManager()


def verify_swagger_credentials(
        credentials: HTTPBasicCredentials = Depends(security),
        request: Request = None
) -> str:
    """
    Улучшенная функция проверки учетных данных

    Включает:
    - Защиту от брутфорс-атак
    - Подробное логирование
    - Контекстную информацию о запросах

    Args:
        credentials: Учетные данные HTTP Basic Auth
        request: Контекст HTTP запроса

    Returns:
        str: Имя пользователя при успешной аутентификации
    """
    return auth_manager.authenticate_user(credentials, request)