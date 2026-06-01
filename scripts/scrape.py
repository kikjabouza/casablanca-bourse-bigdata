"""
Script pour lancer le scraping principal

Usage:
  python scripts/scrape.py              # Scraping complet
  python scripts/scrape.py --daily      # Mise à jour quotidienne
  python scripts/scrape.py --overview   # Market overview uniquement

Voir aussi: python -m src.main
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import main

if __name__ == "__main__":
    main()
