"""
Flow Prefect : Market Overview
Schedule : toutes les 2 minutes (pendant les heures de marché)
Sauvegarde :
  - daily_indices, market_stats, top_movers (mis à jour à chaque exécution)
  - intraday_indices (snapshot horodaté — 1 ligne par 2 minutes)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from typing import Any, Dict

from prefect import flow, get_run_logger, task

from src.scrapers.market_overview_scraper import MarketOverviewScraper
from src.storage.cassandra_client import CassandraClient


@task(name="scrape-market-overview", retries=3, retry_delay_seconds=15)
def scrape_market_overview_task() -> Dict[str, Any]:
    """Scrape la vue globale du marché et sauvegarde les données quotidiennes."""
    scraper = MarketOverviewScraper(save_to_cassandra=True)
    return scraper.scrape_market_overview()


@task(name="save-intraday-snapshot")
def save_intraday_task(market_data: Dict[str, Any]) -> None:
    """
    Sauvegarde un snapshot intraday dans la table intraday_indices.
    Format timestamp: HH:MM (1 point toutes les 2 minutes).
    """
    if not market_data:
        return
    client = CassandraClient()
    now = datetime.now()
    timestamp = now.strftime("%H:%M")
    trade_date = market_data.get("date", now.date())

    for index_name, index_data in market_data.get("indices", {}).items():
        client.save_intraday_index(
            index_name=index_name,
            trade_date=trade_date,
            timestamp=timestamp,
            value=index_data.get("value", 0.0),
        )


@flow(name="market-overview-flow", description="Mise à jour du market overview toutes les 2 minutes")
def market_overview_flow() -> None:
    logger = get_run_logger()

    market_data = scrape_market_overview_task()

    if market_data:
        save_intraday_task(market_data)
        masi = market_data.get("indices", {}).get("MASI", {}).get("value", "N/A")
        logger.info(
            f"Overview mis a jour a {datetime.now().strftime('%H:%M')} — "
            f"MASI={masi}"
        )
    else:
        logger.warning("Aucune donnee recue du scraper market overview")


if __name__ == "__main__":
    market_overview_flow()
