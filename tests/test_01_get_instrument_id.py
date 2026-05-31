"""
Test 1: Vérifier la récupération des IDs des instruments
"""

import sys
import json
from pathlib import Path

# Ajouter le chemin parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.utils.logger import setup_logger, get_logger

# Configuration des logs
setup_logger()
logger = get_logger(__name__)

def test_get_ids():
    """Teste la récupération des IDs pour plusieurs tickers"""
    print("\n" + "="*60)
    print("TEST 1: RÉCUPÉRATION DES IDs DES INSTRUMENTS")
    print("="*60)
    
    scraper = HistoricalDataScraper()
    
    # Tickers à tester
    test_tickers = ['MNG', 'BCP', 'ATW', 'IAM', 'AGM']
    results = {}
    
    for ticker in test_tickers:
        print(f"\n🔍 Recherche de l'ID pour {ticker}...")
        instrument_id = scraper.get_instrument_id(ticker)
        
        if instrument_id:
            print(f"   ✅ ID trouvé: {instrument_id}")
            results[ticker] = instrument_id
        else:
            print(f"   ❌ ID non trouvé")
            results[ticker] = None
    
    # Sauvegarder les résultats
    output_file = Path(__file__).parent / "data" / "instruments_ids.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans {output_file}")
    
    # Résumé
    print("\n" + "-"*40)
    print("RÉSUMÉ:")
    found = sum(1 for v in results.values() if v)
    print(f"✅ IDs trouvés: {found}/{len(test_tickers)}")
    
    return results

if __name__ == "__main__":
    test_get_ids()
