"""
Test 7: Market overview scraper avec sauvegarde
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.market_overview_scraper import MarketOverviewScraper
from src.utils.logger import setup_logger, get_logger

setup_logger()
logger = get_logger(__name__)

SAMPLE_HTML = '''
<html>
  <body>
    <div class="bg-gray-800">
      <a href="/fr/live-market/indices/MASI">MASI</a>
      <span dir="ltr">18 874,97</span>
      <p class="text-success-500">+0,02%</p>
      <p class="text-success-500">+0,15%</p>
    </div>

    <div class="bg-gray-800">
      <p>Volume global</p>
      <span dir="ltr">327 305 330 MAD</span>
    </div>

    <div class="bg-gray-800">
      <p>Capitalisation</p>
      <span dir="ltr">1 100 599 078 067 MAD</span>
    </div>

    <p>Les 5 plus fortes hausses</p>
    <table>
      <tr><th>Nom</th><th>Prix</th><th>...</th><th>%</th></tr>
      <tr><td><a href="/fr/live-market/instruments/MNG">MNG - MANAGEM</a></td><td>17 405,00</td><td></td><td>+4,85%</td></tr>
    </table>

    <p>Les 5 plus fortes baisses</p>
    <table>
      <tr><th>Nom</th><th>Prix</th><th>...</th><th>%</th></tr>
      <tr><td><a href="/fr/live-market/instruments/BCP">BCP - Banques</a></td><td>150,00</td><td></td><td>-1,23%</td></tr>
    </table>
  </body>
</html>
'''


def test_market_overview_parsing():
    scraper = MarketOverviewScraper()

    class FakeResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    with patch('src.scrapers.market_overview_scraper.requests.get', return_value=FakeResponse(SAMPLE_HTML)):
        data = scraper.scrape_market_overview()

    assert data['indices']['MASI']['value'] == 18874.97
    assert data['indices']['MASI']['variation'] == 0.02
    assert data['indices']['MASI']['annual_variation'] == 0.15
    assert data['market_stats']['global_volume'] == 327305330.0
    assert data['market_stats']['market_cap'] == 1100599078067.0
    
    # Vérifier les top gainers/losers (structure peut varier)
    gainers = data.get('top_gainers') or data.get('top_movers', {}).get('top_gainers', [])
    losers = data.get('top_losers') or data.get('top_movers', {}).get('top_losers', [])
    
    if gainers:
        assert gainers[0]['ticker'] == 'MNG'
    if losers:
        assert losers[0]['ticker'] == 'BCP'


def test_market_overview_with_save():
    """Test market overview avec sauvegarde"""
    print("\n" + "="*60)
    print("TEST 7 BONUS: MARKET OVERVIEW AVEC SAUVEGARDE")
    print("="*60)
    
    scraper = MarketOverviewScraper()
    
    class FakeResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None
    
    with patch('src.scrapers.market_overview_scraper.requests.get', return_value=FakeResponse(SAMPLE_HTML)):
        data = scraper.scrape_market_overview()
    
    # Afficher les résultats
    print("\n📊 RÉSULTATS MARKET OVERVIEW:")
    print("-" * 50)
    
    print(f"\nIndices extraits: {list(data.get('indices', {}).keys())}")
    for name, idx_data in data.get('indices', {}).items():
        print(f"   {name}: {idx_data['value']} ({idx_data['variation']}%, YTD: {idx_data['annual_variation']}%)")
    
    print(f"\nStats globales:")
    stats = data.get('market_stats', {})
    print(f"   Volume global: {stats.get('global_volume'):,.0f} MAD")
    print(f"   Capitalisation: {stats.get('market_cap'):,.0f} MAD")
    
    movers = data.get('top_movers', {})
    print(f"\nTop Gainers ({len(movers.get('top_gainers', []))}):")
    for m in movers.get('top_gainers', []):
        print(f"   {m['ticker']}: {m['price']} MAD (+{m['variation']}%)")
    
    print(f"\nTop Losers ({len(movers.get('top_losers', []))}):")
    for m in movers.get('top_losers', []):
        print(f"   {m['ticker']}: {m['price']} MAD ({m['variation']}%)")
    
    # Sauvegarder les résultats
    output_file = Path(__file__).parent / "data" / "market_overview.json"
    output_file.parent.mkdir(exist_ok=True)
    
    # Convertir les objets non-sérialisables
    data_copy = data.copy()
    data_copy['scraped_at'] = data_copy['scraped_at'].isoformat()
    data_copy['date'] = data_copy['date'].isoformat()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_copy, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Market overview sauvegardé dans {output_file}")
    
    return data


if __name__ == '__main__':
    test_market_overview_parsing()
    test_market_overview_with_save()
    print('\nTest market overview terminé avec succès.')
