"""
Flow Prefect : Données historiques
Deux modes:
  - historical_initial_flow : chargement d'1 an complet (à exécuter 1 seule fois)
  - historical_daily_flow   : ajout du dernier jour (schedule: chaque jour à 19h00)

Instruments ciblés : 10 instruments configurés dans TRACKED_INSTRUMENTS (docker-compose.yml / .env)
Sauvegarde : table historical_prices (OHLC + volume ajusté)
"""
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from prefect import flow, get_run_logger, task

from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.utils.config import Config


@task(name="scrape-historical", retries=3, retry_delay_seconds=30)
def scrape_historical_task(
    ticker: str, start_date: str, end_date: str
) -> List[Any]:
    """Scrape et sauvegarde les données historiques d'un instrument."""
    scraper = HistoricalDataScraper()
    return scraper.scrape_historical_data(
        ticker=ticker, start_date=start_date, end_date=end_date
    )


# ─── Flow initial (1 an complet) ─────────────────────────────────────────────

@flow(
    name="historical-initial-flow",
    description="Chargement initial: 1 an d'historique pour les 10 instruments suivis (exécution unique)",
)
def historical_initial_flow() -> None:
    """
    À exécuter UNE SEULE FOIS après le premier démarrage.
    Charge les 365 derniers jours pour chaque instrument suivi.
    Durée estimée: 5-15 minutes selon l'API.
    """
    logger = get_run_logger()
    config = Config()
    start_date = (date.today() - timedelta(days=365)).isoformat()
    end_date = date.today().isoformat()

    logger.info(f"Chargement initial: {start_date} -> {end_date}")
    logger.info(f"Instruments: {config.TRACKED_INSTRUMENTS}")

    for ticker in config.TRACKED_INSTRUMENTS:
        records = scrape_historical_task(ticker, start_date=start_date, end_date=end_date)
        logger.info(f"{ticker}: {len(records)} enregistrements charges")


# ─── Flow quotidien (dernier jour uniquement) ─────────────────────────────────

@flow(
    name="historical-daily-flow",
    description="Ajout quotidien du dernier jour d'historique pour les 10 instruments suivis",
)
def historical_daily_flow() -> None:
    """
    Schedule: 1 fois par jour à 19h00 (après la mise à jour des détails).
    Ajoute uniquement les données du jour ouvré précédent.
    """
    logger = get_run_logger()
    config = Config()
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    today_str = today.isoformat()

    logger.info(f"Mise a jour historique du {yesterday} au {today_str}")

    for ticker in config.TRACKED_INSTRUMENTS:
        records = scrape_historical_task(ticker, start_date=yesterday, end_date=today_str)
        logger.info(f"{ticker}: {len(records)} nouveau(x) enregistrement(s)")


if __name__ == "__main__":
    # Par défaut, exécute le flow quotidien
    historical_daily_flow()
