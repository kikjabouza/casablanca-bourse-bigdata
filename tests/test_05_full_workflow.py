"""
Test 5: Workflow complet avec plusieurs instruments
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.utils.logger import setup_logger, get_logger

setup_logger()
logger = get_logger(__name__)

def test_full_workflow(limit=3):
    """
    Test complet du workflow avec un nombre limité d'instruments
    limit: nombre d'instruments à tester (défaut: 3)
    """
    print("\n" + "="*60)
    print(f"TEST 5: WORKFLOW COMPLET ({limit} premiers instruments)")
    print("="*60)
    
    # 1. Lire la liste des instruments depuis le fichier sauvegardé
    instruments_file = Path(__file__).parent / "data" / "all_instruments.json"
    
    if not instruments_file.exists():
        print("❌ Fichier des instruments non trouvé. Lancez d'abord test_03_instruments_list.py")
        return
    
    with open(instruments_file, 'r', encoding='utf-8') as f:
        all_instruments = json.load(f)
    
    # Prendre seulement les X premiers (actions uniquement, pas d'obligations)
    instruments = [i for i in all_instruments if not i['ticker'].startswith('O')][:limit]
    
    print(f"\n📋 Test sur {len(instruments)} instruments: {[i['ticker'] for i in instruments]}")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'instruments_tested': [],
        'summary': {}
    }
    
    historical_scraper = HistoricalDataScraper()
    details_scraper = InstrumentDetailsScraper()
    
    for i, instrument in enumerate(instruments, 1):
        ticker = instrument['ticker']
        print(f"\n{'='*40}")
        print(f"📊 Instrument {i}/{len(instruments)}: {ticker}")
        print(f"{'='*40}")
        
        instrument_result = {
            'ticker': ticker,
            'id': None,
            'details': None,
            'historical_count': 0,
            'success': False
        }
        
        # Étape 1: Récupérer l'ID
        print(f"  1️⃣ Récupération de l'ID...")
        instrument_id = historical_scraper.get_instrument_id(ticker)
        
        if instrument_id:
            print(f"     ✅ ID: {instrument_id}")
            instrument_result['id'] = instrument_id
        else:
            print(f"     ❌ ID non trouvé, passage au suivant")
            results['instruments_tested'].append(instrument_result)
            continue
        
        # Étape 2: Récupérer les détails
        print(f"  2️⃣ Récupération des détails...")
        details = details_scraper.scrape_instrument(ticker)
        
        if details:
            print(f"     ✅ Prix: {details.get('current_price')} MAD")
            print(f"     ✅ Variation: {details.get('variation')}%")
            instrument_result['details'] = {
                'price': details.get('current_price'),
                'variation': details.get('variation'),
                'volume': details.get('volume'),
                'market_cap': details.get('market_cap')
            }
        else:
            print(f"     ⚠️ Détails non récupérés")
        
        # Étape 3: Récupérer l'historique (limité)
        print(f"  3️⃣ Récupération de l'historique (limité à 30 jours)...")
        
        original_start = historical_scraper.config.DEFAULT_START_DATE
        historical_scraper.config.DEFAULT_START_DATE = "2026-04-01"
        
        try:
            historical = historical_scraper.scrape_historical_data(ticker)
            if historical:
                print(f"     ✅ {len(historical)} jours récupérés")
                instrument_result['historical_count'] = len(historical)
                instrument_result['success'] = True
            else:
                print(f"     ⚠️ Aucune donnée historique")
        finally:
            historical_scraper.config.DEFAULT_START_DATE = original_start
        
        results['instruments_tested'].append(instrument_result)
        
        # Attendre entre les instruments
        time.sleep(1)
    
    # Résumé final
    print("\n" + "="*60)
    print("📊 RÉSUMÉ FINAL")
    print("="*60)
    
    successful = [r for r in results['instruments_tested'] if r['success']]
    print(f"\n✅ Instruments réussis: {len(successful)}/{len(instruments)}")
    
    for r in successful:
        print(f"   - {r['ticker']}: ID={r['id']}, {r['historical_count']} jours, Prix={r['details'].get('price') if r['details'] else 'N/A'}")
    
    results['summary'] = {
        'total_tested': len(instruments),
        'successful': len(successful),
        'failed': len(instruments) - len(successful)
    }
    results['end_time'] = datetime.now().isoformat()
    
    # Sauvegarder les résultats
    output_file = Path(__file__).parent / "data" / "workflow_results.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Résultats complets sauvegardés dans {output_file}")
    
    return results

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    test_full_workflow(limit)
