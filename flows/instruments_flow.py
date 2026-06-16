"""
Flow Prefect : Liste des instruments
Schedule : 1 fois par jour à 18h00 (après clôture du marché)
Logique : scrape la liste complète + INSERT uniquement si changements détectés
"""
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from prefect import flow, get_run_logger, task

from src.scrapers.instruments_list_scraper import InstrumentsListScraper
from src.storage.cassandra_client import CassandraClient


@task(name="scrape-all-instruments", retries=3, retry_delay_seconds=30)
def scrape_instruments_task() -> List[Dict]:
    """Scrape la liste complète des instruments via API."""
    scraper = InstrumentsListScraper()
    # On ne sauvegarde pas ici — la comparaison se fait dans le flow
    return scraper._scrape_from_api() or scraper._scrape_from_html()


@task(name="get-existing-instruments")
def get_existing_task() -> Dict[str, Dict]:
    """Lit les instruments existants dans Cassandra."""
    client = CassandraClient()
    return client.get_all_instruments()


@task(name="save-changed-instruments")
def save_changed_task(new_instruments: List[Dict], existing: Dict[str, Dict]) -> int:
    """
    Compare la liste neuve avec l'existant.
    INSERT uniquement si ticker inconnu ou name/url modifié.
    Retourne le nombre d'instruments mis à jour.
    """
    client = CassandraClient()
    changed = 0
    for inst in new_instruments:
        ticker = inst.get("ticker", "")
        ex = existing.get(ticker)
        if not ex or ex.get("name") != inst.get("name") or ex.get("url") != inst.get("url"):
            client.save_instrument(inst)
            changed += 1
    return changed


@flow(name="instruments-daily-flow", description="Mise à jour quotidienne de la liste des instruments")
def instruments_flow() -> None:
    logger = get_run_logger()

    new_instruments = scrape_instruments_task()
    existing = get_existing_task()
    changed = save_changed_task(new_instruments, existing)

    logger.info(
        f"Instruments: {len(new_instruments)} scrapes, "
        f"{changed} inseres/mis a jour dans Cassandra"
    )


if __name__ == "__main__":
    instruments_flow()
