"""
Chargement initial des données — À exécuter UNE SEULE FOIS.
Ordre d'exécution:
  1. docker-compose up -d          (démarrer la stack)
  2. python scripts/init_cassandra.py  (optionnel si cassandra-init l'a fait)
  3. python scripts/run_initial_load.py  (ce script)
  4. python flows/deployments.py    (déployer les flows Prefect)

Ce script:
  - Charge la liste complète des instruments dans Cassandra
  - Charge 1 an d'historique OHLC pour ATW, BCP, MNG
"""
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.scrapers.instruments_list_scraper import InstrumentsListScraper
from src.utils.config import Config
from src.utils.logger import get_logger, setup_logger

setup_logger()
logger = get_logger(__name__)


def run_initial_load() -> None:
    config = Config()
    start_date = (date.today() - timedelta(days=365)).isoformat()
    end_date = date.today().isoformat()

    logger.info("=" * 60)
    logger.info("CHARGEMENT INITIAL DES DONNEES")
    logger.info(f"Periode historique: {start_date} -> {end_date}")
    logger.info(f"Instruments suivis: {config.TRACKED_INSTRUMENTS}")
    logger.info("=" * 60)

    # Étape 1: Liste complète des instruments
    logger.info("\n[1/2] Chargement de la liste des instruments...")
    list_scraper = InstrumentsListScraper()
    instruments = list_scraper.scrape_instruments_list()
    logger.info(f"  -> {len(instruments)} instruments charges dans Cassandra")

    # Étape 2: Historique 1 an pour les 3 instruments suivis
    logger.info(f"\n[2/2] Chargement de l'historique ({start_date} -> {end_date})...")
    hist_scraper = HistoricalDataScraper()

    for ticker in config.TRACKED_INSTRUMENTS:
        logger.info(f"  -> {ticker}: chargement en cours...")
        try:
            records = hist_scraper.scrape_historical_data(
                ticker, start_date=start_date, end_date=end_date
            )
            logger.info(f"  -> {ticker}: {len(records)} enregistrements")
        except Exception as exc:
            logger.error(f"  -> {ticker}: ERREUR - {exc}")

    logger.info("\n" + "=" * 60)
    logger.info("CHARGEMENT INITIAL TERMINE")
    logger.info("Prochaine etape: python flows/deployments.py")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_initial_load()
