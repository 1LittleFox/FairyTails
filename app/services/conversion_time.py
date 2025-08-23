import math

def seconds_to_hms(seconds):
    """
    Конвертирует секунды в формат ЧЧ:ММ:СС

    Args:
        seconds (int): количество секунд

    Returns:
        str: время в формате ЧЧ:ММ:СС
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def seconds_to_minutes(seconds):
    """
    Конвертирует секунды в минуты с округлением в большую сторону

    Args:
        seconds (int): количество секунд

    Returns:
        int: количество минут
    """
    remainder_seconds = seconds % 60

    if remainder_seconds < 30:
        return math.floor(seconds / 60)

    return math.ceil(seconds / 60)
