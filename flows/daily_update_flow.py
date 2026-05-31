# flows/daily_update_flow.py
import time
from datetime import date

from prefect import flow, get_run_logger, task

from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.scrapers.instruments_list_scraper import InstrumentsListScraper
from src.scrapers.market_overview_scraper import MarketOverviewScraper
from src.storage.cassandra_client import CassandraClient
from src.utils.config import Config
from src.utils.logger import setup_logger


@task(name="daily-update-instrument", retries=3, retry_delay_seconds=20, log_prints=True)
def daily_update_instrument(ticker: str):
    details_scraper = InstrumentDetailsScraper()
    historical_scraper = HistoricalDataScraper()

    details_scraper.scrape_instrument(ticker)

    today = date.today().isoformat()
    historical_scraper.scrape_historical_data(ticker, start_date=today)
    return ticker


@task(name="daily-update-market-overview", retries=3, retry_delay_seconds=20, log_prints=True)
def daily_update_market_overview():
    scraper = MarketOverviewScraper()
    return scraper.scrape_market_overview(enrich_top_movers=True)


@flow(name="daily-update-flow", description="Mise à jour quotidienne après clôture du marché")
def daily_update_flow():
    setup_logger()
    logger = get_run_logger()
    config = Config()

    logger.info("Démarrage de la mise à jour quotidienne")
    CassandraClient()

    instruments = InstrumentsListScraper().scrape_instruments_list()
    if not instruments:
        logger.error("Aucun instrument trouvé")
        return

    for index, instrument in enumerate(instruments, 1):
        ticker = instrument["ticker"]
        logger.info(f"[{index}/{len(instruments)}] Mise à jour de {ticker}")
        daily_update_instrument(ticker)
        time.sleep(config.REQUEST_DELAY)

    daily_update_market_overview()
    logger.info("Mise à jour quotidienne terminée")


if __name__ == "__main__":
    daily_update_flow()
