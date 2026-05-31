"""
Test 2: Récupération des données historiques pour un instrument
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.utils.logger import setup_logger, get_logger

setup_logger()
logger = get_logger(__name__)

def test_historical_data(ticker="MNG", limit_days=30):
    """
    Teste la récupération des données historiques
    limit_days: limite à X jours pour le test (évite de tout scraper)
    """
    print("\n" + "="*60)
    print(f"TEST 2: DONNÉES HISTORIQUES POUR {ticker}")
    print("="*60)
    
    scraper = HistoricalDataScraper()
    
    # 1. Récupérer l'ID
    print(f"\n1️⃣ Récupération de l'ID pour {ticker}...")
    instrument_id = scraper.get_instrument_id(ticker)
    
    if not instrument_id:
        print(f"❌ Impossible de continuer: ID non trouvé pour {ticker}")
        return None
    
    print(f"   ✅ ID trouvé: {instrument_id}")
    
    # 2. Récupérer l'historique (limité à limit_days pour le test)
    print(f"\n2️⃣ Récupération de l'historique (limité à {limit_days} jours)...")
    
    # Modifier temporairement la date de début pour limiter les données
    original_start_date = scraper.config.DEFAULT_START_DATE
    scraper.config.DEFAULT_START_DATE = "2026-04-01"  # Seulement avril-mai 2026
    
    try:
        all_records = scraper.scrape_historical_data(ticker)
        
        if all_records:
            print(f"   ✅ {len(all_records)} enregistrements récupérés")
            
            # Afficher les 5 premiers et 5 derniers
            print("\n📊 APERÇU DES DONNÉES:")
            print("-" * 80)
            print(f"{'Date':<12} {'Close':<12} {'Open':<12} {'High':<12} {'Low':<12} {'Volume':<15}")
            print("-" * 80)
            
            for record in all_records[:5]:
                print(f"{record.get('date', '')[:10]:<12} "
                      f"{(record.get('close_price') or 0):<12.2f} "
                      f"{(record.get('open_price') or 0):<12.2f} "
                      f"{(record.get('high_price') or 0):<12.2f} "
                      f"{(record.get('low_price') or 0):<12.2f} "
                      f"{(record.get('volume') or 0):<15.2f}")
            
            if len(all_records) > 10:
                print("   ...")
                for record in all_records[-5:]:
                    print(f"{record.get('date', '')[:10]:<12} "
                          f"{(record.get('close_price') or 0):<12.2f} "
                          f"{(record.get('open_price') or 0):<12.2f} "
                          f"{(record.get('high_price') or 0):<12.2f} "
                          f"{(record.get('low_price') or 0):<12.2f} "
                          f"{(record.get('volume') or 0):<15.2f}")
            
            # Statistiques
            closes = [r['close_price'] for r in all_records if r.get('close_price') is not None]
            if closes:
                print("\n📈 STATISTIQUES:")
                print(f"   Prix min: {min(closes):.2f} MAD")
                print(f"   Prix max: {max(closes):.2f} MAD")
                print(f"   Prix moyen: {sum(closes)/len(closes):.2f} MAD")
                if closes[0] != 0:
                    print(f"   Variation période: {((closes[-1] - closes[0]) / closes[0] * 100):.2f}%")
            
            # Sauvegarder dans un fichier JSON
            output_file = Path(__file__).parent / "data" / f"{ticker}_historical.json"
            output_file.parent.mkdir(exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Données sauvegardées dans {output_file}")
            
            return all_records
        else:
            print(f"   ❌ Aucune donnée récupérée")
            return None
            
    finally:
        # Restaurer la configuration
        scraper.config.DEFAULT_START_DATE = original_start_date

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "MNG"
    test_historical_data(ticker)
