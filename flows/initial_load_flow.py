# flows/initial_load_flow.py
# Ajouter ces 3 lignes au tout début, AVANT les autres imports

import sys
from pathlib import Path
# Ajouter le dossier parent au chemin Python
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensuite les autres imports
from prefect import flow, get_run_logger, task
# flows/initial_load_flow.py
import time

from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.scrapers.instruments_list_scraper import InstrumentsListScraper
from src.scrapers.market_overview_scraper import MarketOverviewScraper
from src.storage.cassandra_client import CassandraClient
from src.utils.config import Config
from src.utils.logger import setup_logger


@task(name="fetch-instruments-list", retries=3, retry_delay_seconds=30, log_prints=True)
def fetch_instruments_list():
    scraper = InstrumentsListScraper()
    return scraper.scrape_instruments_list()


@task(name="fetch-instrument-details", retries=3, retry_delay_seconds=20, log_prints=True)
def fetch_instrument_details(ticker: str):
    scraper = InstrumentDetailsScraper()
    return scraper.scrape_instrument(ticker)


@task(name="fetch-historical-data", retries=3, retry_delay_seconds=30, log_prints=True)
def fetch_historical_data(ticker: str):
    scraper = HistoricalDataScraper()
    return scraper.scrape_historical_data(ticker)


@task(name="fetch-market-overview", retries=3, retry_delay_seconds=20, log_prints=True)
def fetch_market_overview():
    scraper = MarketOverviewScraper()
    return scraper.scrape_market_overview(enrich_top_movers=True)


@flow(name="initial-load-flow", description="Chargement initial complet des données boursières")
def initial_load_flow(limit: int | None = None):
    setup_logger()
    logger = get_run_logger()
    config = Config()

    logger.info("Démarrage du chargement initial")
    CassandraClient()

    instruments = fetch_instruments_list()
    if not instruments:
        logger.error("Aucun instrument trouvé")
        return

    if limit is not None:
        instruments = instruments[:limit]

    logger.info(f"{len(instruments)} instruments à traiter")

    for index, instrument in enumerate(instruments, 1):
        ticker = instrument["ticker"]
        logger.info(f"[{index}/{len(instruments)}] Traitement de {ticker}")
        fetch_instrument_details(ticker)
        time.sleep(config.REQUEST_DELAY)
        fetch_historical_data(ticker)
        time.sleep(config.BULK_REQUEST_DELAY)

    fetch_market_overview()
    logger.info("Chargement initial terminé")


if __name__ == "__main__":
    initial_load_flow()
