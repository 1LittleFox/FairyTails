
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