"""
Test 4: Récupération des détails d'un instrument
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.utils.logger import setup_logger, get_logger

setup_logger()
logger = get_logger(__name__)

def test_instrument_details(ticker="MNG"):
    """Teste la récupération des détails d'un instrument"""
    print("\n" + "="*60)
    print(f"TEST 4: DÉTAILS DE L'INSTRUMENT {ticker}")
    print("="*60)
    
    scraper = InstrumentDetailsScraper()
    
    print(f"\n🔍 Scraping des détails pour {ticker}...")
    details = scraper.scrape_instrument(ticker)
    
    if not details:
        print(f"❌ Aucun détail récupéré pour {ticker}")
        return None
    
    print("\n✅ Détails récupérés avec succès")
    
    # Afficher les informations
    print("\n📊 INFORMATIONS STATIQUES:")
    print("-" * 40)
    print(f"   Ticker: {details.get('ticker')}")
    print(f"   ISIN: {details.get('isin')}")
    print(f"   Secteur: {details.get('sector')}")
    print(f"   Date d'introduction: {details.get('listing_date')}")
    print(f"   Nombre de titres: {details.get('shares_count')}")
    print(f"   Valeur nominale: {details.get('nominal_value')} MAD")
    print(f"   Cycle de négociation: {details.get('trading_cycle')}")
    print(f"   Devise: {details.get('currency')}")
    
    print("\n📈 DONNÉES DE SÉANCE:")
    print("-" * 40)
    print(f"   Cours actuel: {details.get('current_price')} MAD")
    print(f"   Variation: {details.get('variation')}%")
    print(f"   Ouverture: {details.get('opening_price')} MAD")
    print(f"   Plus haut: {details.get('high_price')} MAD")
    print(f"   Plus bas: {details.get('low_price')} MAD")
    print(f"   Clôture veille: {details.get('prev_close')} MAD")
    print(f"   Capitalisation: {details.get('market_cap')} MAD")
    print(f"   Volume: {details.get('volume')} MAD")
    print(f"   Quantité échangée: {details.get('quantity')} MAD")
    print(f"   Nombre de transactions: {details.get('trades_count')} MAD")
    
    print("\n📉 VARIATIONS HISTORIQUES:")
    print("-" * 40)
    print(f"   Depuis début d'année: {details.get('var_ytd')}%")
    print(f"   Depuis 2023: {details.get('var_2023')}%")
    print(f"   Depuis 2021: {details.get('var_2021')}%")
    
    # Sauvegarder dans un fichier JSON
    output_file = Path(__file__).parent / "data" / f"{ticker}_details.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(details, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Détails sauvegardés dans {output_file}")
    
    return details

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "MNG"
    test_instrument_details(ticker)
