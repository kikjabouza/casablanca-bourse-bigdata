"""
Test 6: MASI realtime scraper avec sauvegarde
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.masi_realtime_scraper import MASIRealtimeScraper
from src.utils.logger import setup_logger, get_logger
from src.utils.config import Config

setup_logger()
logger = get_logger(__name__)


def test_scrape_single_index():
    """Teste la récupération d'un point MASI en temps réel"""
    sample_json = {
        'data': [
            {
                'attributes': {
                    'indexValue': '18874.97',
                    'transactTime': '2026-05-31T16:00:00Z'
                }
            }
        ]
    }

    class FakeResponse:
        def __init__(self, json_data):
            self._json = json_data

        def raise_for_status(self):
            return None

        def json(self):
            return self._json

    scraper = MASIRealtimeScraper()

    with patch('src.scrapers.masi_realtime_scraper.requests.get', return_value=FakeResponse(sample_json)):
        point = scraper.scrape_single_index('MASI')

    assert point is not None
    assert point['index_name'] == 'MASI'
    assert point['value'] == 18874.97
    assert point['timestamp'] == '2026-05-31T16:00:00Z'


def test_get_latest_value():
    """Teste la lecture de la dernière valeur depuis le stub Cassandra"""
    scraper = MASIRealtimeScraper()
    scraper.cassandra.execute = lambda query, params=None: [{'value': 14500.0}]

    latest = scraper.get_latest_value('MASI')
    assert latest == 14500.0


def test_masi_realtime_with_save():
    """Test MASI avec sauvegarde des résultats en temps réel"""
    print("\n" + "="*60)
    print("TEST 6 BONUS: MASI TEMPS RÉEL AVEC SAUVEGARDE")
    print("="*60)
    
    from src.utils.config import Config
    
    config = Config()
    indices = ['MASI', 'MASI20', 'MASI_ESG']
    
    results = {
        'scraped_at': datetime.now().isoformat(),
        'points': []
    }
    
    scraper = MASIRealtimeScraper()
    
    for index_name in indices:
        print(f"\n🔍 Scraping {index_name}...")
        point = scraper.scrape_single_index(index_name)
        
        if point:
            print(f"   ✅ {index_name}: {point['value']:.2f} pts (at {point['timestamp']})")
            # Enlever le champ "scraped_at" qui n'est pas sérialisable
            point_to_save = {
                'index_name': point['index_name'],
                'value': point['value'],
                'timestamp': point['timestamp']
            }
            results['points'].append(point_to_save)
        else:
            print(f"   ⚠️ {index_name}: non disponible")
    
    # Sauvegarder les résultats
    output_file = Path(__file__).parent / "data" / "masi_realtime.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Résultats sauvegardés dans {output_file}")
    print(f"✅ {len(results['points'])} points MASI sauvegardés")
    
    return results


if __name__ == '__main__':
    test_scrape_single_index()
    test_get_latest_value()
    test_masi_realtime_with_save()
    print('\nTests MASI realtime terminés avec succès.')
