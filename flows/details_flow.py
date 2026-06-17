"""
Flow Prefect : Détails des instruments
Schedule : toutes les 15 minutes
Instruments ciblés : 10 instruments configurés dans TRACKED_INSTRUMENTS (docker-compose.yml / .env)
Sauvegarde : instruments_static + daily_prices (upsert de la séance du jour)
"""
import sys
import time
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from prefect import flow, get_run_logger, task

from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.utils.config import Config


@task(name="scrape-instrument-details", retries=3, retry_delay_seconds=20)
def scrape_details_task(ticker: str) -> Dict[str, Any]:
    """Scrape et sauvegarde les détails d'un instrument."""
    scraper = InstrumentDetailsScraper()
    return scraper.scrape_instrument(ticker)


@flow(name="details-flow", description="Mise à jour des détails de 10 instruments toutes les 15 min")
def details_flow() -> None:
    logger = get_run_logger()
    config = Config()
    tickers = config.TRACKED_INSTRUMENTS

    logger.info(f"Scraping details pour: {tickers}")

    for ticker in tickers:
        data = scrape_details_task(ticker)
        if data:
            logger.info(
                f"{ticker}: cours={data.get('current_price')} MAD, "
                f"variation={data.get('variation')}%, "
                f"volume={data.get('volume')}"
            )
        else:
            logger.warning(f"{ticker}: aucune donnee recue")
        time.sleep(1)  # Petite pause entre instruments


if __name__ == "__main__":
    details_flow()
