import logging
import sys
import io


def setup_logger(level=logging.INFO):
    """Configure le logging pour toute l'application (compatible Windows UTF-8)."""
    if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bourse_scraper.log', encoding='utf-8'),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger nommé."""
    return logging.getLogger(name)
