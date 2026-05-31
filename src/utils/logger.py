# src/utils/logger.py
import logging
import sys
import io

def setup_logger(level=logging.INFO):
    """Configure le logging pour toute l'application"""
    # Remplacer sys.stdout par un stream UTF-8 compatible Windows
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bourse_scraper.log', encoding='utf-8')
        ]
    )

def get_logger(name):
    """Retourne un logger configuré"""
    return logging.getLogger(name)