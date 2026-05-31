# scripts/load_data.py
"""
Script de chargement initial SANS Prefect
Charge les données dans Cassandra (mode test = fichiers JSON)
"""

import sys
from pathlib import Path
import time
import json

# Ajouter le dossier parent au chemin
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.scrapers.market_overview_scraper import MarketOverviewScraper
from src.utils.logger import setup_logger, get_logger
from src.utils.config import Config

setup_logger()
logger = get_logger(__name__)
config = Config()


def get_instrument_id(ticker: str) -> int:
    """
    Récupère l'ID d'un instrument depuis le fichier JSON ou fallback
    """
    ids_file = Path(__file__).parent.parent / "tests" / "data" / "instruments_ids.json"
    
    if ids_file.exists():
        try:
            with open(ids_file, 'r', encoding='utf-8') as f:
                ids_data = json.load(f)
            if ticker in ids_data:
                return ids_data[ticker]
        except Exception as e:
            logger.warning(f"Erreur lecture IDs: {e}")
    
    # Fallback - IDs connus des tests
    fallback_ids = {
        'MNG': 500,
        'BCP': 509,
        'ATW': 511,
        'IAM': 510,
        'AGM': 491,
        'BOA': 505,
        'CIH': 506,
        'CDM': 507,
        'CFG': 508,
        'AFM': 1,
        'AFI': 2,
        'GAZ': 3,
        'AKT': 4,
        'ADI': 5,
        'ALM': 6,
        'ARD': 7,
        'ATL': 8,
        'ATH': 9,
        'NEJ': 10,
        'BAL': 11,
        'BCI': 12,
        'CRS': 13,
        'CAP': 14,
        'CMA': 15,
        'CMG': 16,
        'COL': 17,
        'CSR': 18,
        'CTM': 19,
        'DRI': 20,
        'DLM': 21,
        'DHO': 22,
        'DIS': 23,
        'DYT': 24,
        'DWY': 25,
        'ADH': 26,
        'NKL': 27,
        'EQD': 28,
        'FBR': 29,
        'HPS': 30,
        'IBC': 31,
        'IMO': 32,
        'INV': 534,
        'JET': 33,
        'LBV': 34,
        'LHM': 35,
        'LES': 36,
        'M2M': 37,
        'MOX': 38,
        'MAB': 39,
        'MLE': 40,
        'MDP': 41,
        'MIC': 42,
        'CMT': 43,
        'MUT': 44,
        'OUL': 45,
        'PRO': 46,
        'SRM': 47,
        'REB': 48,
        'RDS': 49,
        'RIS': 50,
        'S2M': 51,
        'SLF': 52,
        'SAM': 53,
        'SAH': 54,
        'GTM': 55,
        'SMI': 56,
        'SNP': 57,
        'SBM': 58,
        'MSA': 59,
        'SID': 60,
        'SOT': 61,
        'SNA': 62,
        'STR': 63,
        'TQM': 64,
        'TGC': 65,
        'TMA': 66,
        'UMR': 67,
        'VCN': 68,
        'WAA': 69,
        'ZDJ': 70
    }
    
    return fallback_ids.get(ticker, None)


def get_instruments_via_api() -> list:
    """
    Récupère la liste des instruments depuis le fichier JSON des IDs
    """
    instruments = []
    
    # Liste des tickers depuis le fichier IDs
    ids_file = Path(__file__).parent.parent / "tests" / "data" / "instruments_ids.json"
    
    if ids_file.exists():
        try:
            with open(ids_file, 'r', encoding='utf-8') as f:
                ids_data = json.load(f)
            for ticker, instrument_id in ids_data.items():
                instruments.append({
                    'ticker': ticker,
                    'name': ticker,
                    'id': instrument_id
                })
            logger.info(f"✅ {len(instruments)} instruments chargés depuis instruments_ids.json")
            return instruments
        except Exception as e:
            logger.warning(f"Erreur lecture instruments_ids.json: {e}")
    
    # Fallback : liste manuelle des tickers
    fallback_tickers = [
        'MNG', 'BCP', 'ATW', 'IAM', 'AGM', 'BOA', 'CIH', 'CDM', 'CFG',
        'AFM', 'AFI', 'GAZ', 'AKT', 'ADI', 'ALM', 'ARD', 'ATL', 'ATH',
        'NEJ', 'BAL', 'BCI', 'CRS', 'CAP', 'CMA', 'CMG', 'COL', 'CSR',
        'CTM', 'DRI', 'DLM', 'DHO', 'DIS', 'DYT', 'DWY', 'ADH', 'NKL',
        'EQD', 'FBR', 'HPS', 'IBC', 'IMO', 'INV', 'JET', 'LBV', 'LHM',
        'LES', 'M2M', 'MOX', 'MAB', 'MLE', 'MDP', 'MIC', 'CMT', 'MUT',
        'OUL', 'PRO', 'SRM', 'REB', 'RDS', 'RIS', 'S2M', 'SLF', 'SAM',
        'SAH', 'GTM', 'SMI', 'SNP', 'SBM', 'MSA', 'SID', 'SOT', 'SNA',
        'STR', 'TQM', 'TGC', 'TMA', 'UMR', 'VCN', 'WAA', 'ZDJ'
    ]
    
    for ticker in fallback_tickers:
        instrument_id = get_instrument_id(ticker)
        instruments.append({
            'ticker': ticker,
            'name': ticker,
            'id': instrument_id
        })
    
    logger.info(f"⚠️ {len(instruments)} instruments chargés depuis la liste de fallback")
    return instruments


def load_instrument(ticker: str, index: int, total: int) -> dict:
    """
    Charge un instrument complet (détails + historique)
    Retourne un dict avec les résultats
    """
    logger.info(f"[{index}/{total}] Traitement de {ticker}")
    
    result = {
        'ticker': ticker,
        'details_success': False,
        'historical_success': False,
        'historical_count': 0,
        'price': None
    }
    
    # Récupérer l'ID pour l'historique
    instrument_id = get_instrument_id(ticker)
    
    # 1. Détails
    logger.info(f"  📊 Détails pour {ticker}...")
    details_scraper = InstrumentDetailsScraper()
    try:
        details = details_scraper.scrape_instrument(ticker)
        if details:
            result['details_success'] = True
            result['price'] = details.get('current_price')
            logger.info(f"  ✅ Détails OK - Prix: {details.get('current_price', 'N/A')} MAD")
        else:
            logger.warning(f"  ⚠️ Pas de détails pour {ticker}")
    except Exception as e:
        logger.error(f"  ❌ Erreur détails {ticker}: {e}")
    
    time.sleep(config.REQUEST_DELAY)
    
    # 2. Historique
    if instrument_id:
        logger.info(f"  📈 Historique pour {ticker} (ID: {instrument_id})...")
        hist_scraper = HistoricalDataScraper()
        try:
            # Forcer la date de début pour avoir plus de données
            original_start = config.DEFAULT_START_DATE
            config.DEFAULT_START_DATE = "2020-01-01"
            
            historical = hist_scraper.scrape_historical_data(ticker)
            
            # Restaurer la date
            config.DEFAULT_START_DATE = original_start
            
            if historical:
                result['historical_success'] = True
                result['historical_count'] = len(historical)
                logger.info(f"  ✅ Historique OK - {len(historical)} jours")
            else:
                logger.warning(f"  ⚠️ Pas d'historique pour {ticker}")
        except Exception as e:
            logger.error(f"  ❌ Erreur historique {ticker}: {e}")
    else:
        logger.warning(f"  ⚠️ Pas d'ID pour {ticker}, historique ignoré")
    
    time.sleep(config.BULK_REQUEST_DELAY)
    
    return result


def load_market_overview() -> dict:
    """
    Scrape les données de marché globales
    """
    logger.info("🌍 Scraping du market overview...")
    overview_scraper = MarketOverviewScraper()
    try:
        overview = overview_scraper.scrape_market_overview()
        if overview:
            indices = overview.get('indices', {})
            masi = indices.get('MASI', {}).get('value', 'N/A')
            masi20 = indices.get('MASI20', {}).get('value', 'N/A')
            logger.info(f"✅ Market overview OK - MASI: {masi}, MASI20: {masi20}")
            return overview
    except Exception as e:
        logger.error(f"❌ Erreur market overview: {e}")
    
    return {}


def save_summary(results: list, overview: dict, output_file: Path):
    """
    Sauvegarde un résumé du chargement
    """
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_instruments': len(results),
        'details_success': sum(1 for r in results if r['details_success']),
        'historical_success': sum(1 for r in results if r['historical_success']),
        'total_historical_days': sum(r['historical_count'] for r in results),
        'instruments': results,
        'market_overview': {
            'indices': overview.get('indices', {}),
            'market_stats': overview.get('market_stats', {}),
            'top_gainers': overview.get('top_gainers', [])[:3],
            'top_losers': overview.get('top_losers', [])[:3]
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"💾 Résumé sauvegardé dans {output_file}")
    return summary


def main(limit: int = None, ticker: str = None):
    """
    Exécute le chargement initial
    
    Args:
        limit: Nombre maximum d'instruments à traiter (None = tous)
        ticker: Ticker spécifique à traiter (None = tous)
    """
    print("=" * 60)
    print("🚀 CHARGEMENT INITIAL (sans Prefect)")
    print("=" * 60)
    
    # 1. Récupérer la liste des instruments
    logger.info("📋 Récupération de la liste des instruments...")
    
    if ticker:
        # Mode mono-instrument
        instruments = [{'ticker': ticker, 'name': ticker, 'id': get_instrument_id(ticker)}]
        logger.info(f"🔍 Mode mono-instrument: {ticker}")
    else:
        instruments = get_instruments_via_api()
    
    if not instruments:
        logger.error("❌ Aucun instrument trouvé")
        return
    
    logger.info(f"✅ {len(instruments)} instruments à traiter")
    
    # 2. Limiter si demandé
    if limit and limit > 0:
        instruments = instruments[:limit]
        logger.info(f"🔒 Limité à {limit} instruments")
    
    # 3. Traiter chaque instrument
    results = []
    start_time = time.time()
    
    for i, inst in enumerate(instruments, 1):
        ticker_name = inst.get('ticker', inst.get('name', str(inst)))
        result = load_instrument(ticker_name, i, len(instruments))
        results.append(result)
    
    # 4. Market overview
    overview = load_market_overview()
    
    # 5. Sauvegarder le résumé
    output_dir = Path(__file__).parent.parent / "tests" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_file = output_dir / "load_summary.json"
    summary = save_summary(results, overview, summary_file)
    
    # 6. Afficher le résumé final
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DU CHARGEMENT")
    print("=" * 60)
    print(f"Temps écoulé: {elapsed:.1f} secondes")
    print(f"Instruments traités: {summary['total_instruments']}")
    print(f"Détails réussis: {summary['details_success']}/{summary['total_instruments']}")
    print(f"Historique réussi: {summary['historical_success']}/{summary['total_instruments']}")
    print(f"Jours historiques: {summary['total_historical_days']}")
    
    print("\n" + "=" * 60)
    print("✅ CHARGEMENT INITIAL TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Chargement des données Bourse de Casablanca')
    parser.add_argument('--limit', type=int, help='Limite le nombre d\'instruments (pour test)')
    parser.add_argument('--ticker', type=str, help='Ticker spécifique à traiter (ex: MNG)')
    parser.add_argument('--all', action='store_true', help='Traiter tous les instruments')
    
    args = parser.parse_args()
    
    if args.all:
        main(limit=None, ticker=None)
    elif args.ticker:
        main(ticker=args.ticker.upper())
    elif args.limit:
        main(limit=args.limit)
    else:
        # Par défaut : test avec 3 instruments
        print("🔧 Mode par défaut: test avec 3 instruments")
        print("   Utilisez --all pour tout charger, --ticker TICKER pour un instrument")
        main(limit=3)