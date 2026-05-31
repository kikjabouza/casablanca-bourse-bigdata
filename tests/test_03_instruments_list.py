"""
Test 3: Récupération de la liste complète des instruments
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.instruments_list_scraper import InstrumentsListScraper
from src.utils.logger import setup_logger, get_logger

setup_logger()
logger = get_logger(__name__)

def test_instruments_list():
    """Teste la récupération de la liste des instruments"""
    print("\n" + "="*60)
    print("TEST 3: LISTE COMPLÈTE DES INSTRUMENTS")
    print("="*60)
    
    scraper = InstrumentsListScraper()
    
    print("\n🔍 Scraping de la liste des instruments...")
    instruments = scraper.scrape_instruments_list()
    
    # Si le HTML parsing ne fonctionne pas, utiliser les IDs connus
    if not instruments:
        print("⚠️ HTML parsing échoué, utilisation des IDs connus...")
        ids_file = Path(__file__).parent / "data" / "instruments_ids.json"
        if ids_file.exists():
            with open(ids_file, 'r', encoding='utf-8') as f:
                known_ids = json.load(f)
            instruments = [
                {'ticker': ticker, 'name': ticker, 'id': id_val}
                for ticker, id_val in known_ids.items()
            ]
            print(f"✅ {len(instruments)} instruments trouvés via IDs")
        else:
            print("❌ Aucun instrument trouvé et pas de fichier IDs")
            return None
    
    print(f"\n✅ {len(instruments)} instruments trouvés")
    
    # Afficher les 20 premiers
    print("\n📋 APERÇU (20 premiers):")
    print("-" * 50)
    for i, inst in enumerate(instruments[:20], 1):
        print(f"{i:3}. {inst['ticker']:6} - {inst.get('name', inst['ticker'])[:40]}")
    
    # Sauvegarder la liste complète
    output_file = Path(__file__).parent / "data" / "all_instruments.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(instruments, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Liste sauvegardée dans {output_file}")
    
    # Sauvegarder aussi juste les tickers
    tickers = [i['ticker'] for i in instruments]
    ticker_file = Path(__file__).parent / "data" / "tickers.txt"
    with open(ticker_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(tickers))
    
    print(f"💾 Tickers sauvegardés dans {ticker_file}")
    
    return instruments

if __name__ == "__main__":
    test_instruments_list()
