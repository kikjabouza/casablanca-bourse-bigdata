# src/utils/helpers.py
import time
from functools import wraps
from src.utils.logger import get_logger

logger = get_logger(__name__)

def retry(max_attempts=3, delay=1):
    """Décorateur pour réessayer une fonction en cas d'échec"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Tentative {attempt + 1} échouée pour {func.__name__}: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def safe_float(value, default=None):
    """Convertit une valeur en float de manière sécurisée"""
    if value is None:
        return default
    try:
        return float(str(value).replace(',', '.').replace(' ', ''))
    except (ValueError, TypeError):
        return default

def safe_int(value, default=None):
    """Convertit une valeur en int de manière sécurisée"""
    if value is None:
        return default
    try:
        return int(str(value).replace(' ', ''))
    except (ValueError, TypeError):
        return default