"""
Test 3 BIS: Récupération de la liste des instruments via API
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.instruments_list_scraper import InstrumentsListScraper
from src.utils.logger import setup_logger, get_logger

setup_logger()
logger = get_logger(__name__)

def test_instruments_list_via_api():
    """Teste la récupération de la liste d'instruments via l'API JSON ou le HTML."""
    print("\n" + "="*60)
    print("TEST 3 BIS: LISTE DES INSTRUMENTS VIA API JSON")
    print("="*60)

    scraper = InstrumentsListScraper()
    instruments = scraper.scrape_instruments_list()

    if not instruments:
        print("❌ Aucun instrument retourné depuis l'API ou le HTML")
        return None

    print(f"\n✅ {len(instruments)} instruments trouvés")
    print("\n📋 LISTE DES INSTRUMENTS:")
    print("-" * 50)
    for inst in instruments[:30]:
        print(f"   {inst['ticker']:6} - {inst.get('name', '')}")

    output_file = Path(__file__).parent / "data" / "all_instruments.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(instruments, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Liste sauvegardée dans {output_file}")
    return instruments

if __name__ == "__main__":
    test_instruments_list_via_api()
