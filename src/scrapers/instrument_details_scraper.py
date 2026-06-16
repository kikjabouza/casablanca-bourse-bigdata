import urllib3
from datetime import datetime
from typing import Any, Dict

import requests

from src.parsers.html_parser import HTMLParser
from src.storage.cassandra_client import CassandraClient
from src.utils.config import Config
from src.utils.helpers import retry
from src.utils.logger import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


class InstrumentDetailsScraper:
    """Scrape les détails statiques et la séance d'un instrument."""

    def __init__(self):
        self.config = Config()
        self.parser = HTMLParser()
        self.cassandra = CassandraClient()

    @retry(max_attempts=3, delay=5.0)
    def scrape_instrument(self, ticker: str) -> Dict[str, Any]:
        """
        Scrape l'ensemble des données pour un ticker donné.
        Retourne un dict avec toutes les informations disponibles.
        Sauvegarde dans Cassandra (no-op si mode stub).
        """
        url = f"{self.config.INSTRUMENT_BASE_URL}/{ticker}"
        logger.info(f"Scraping {ticker} -> {url}")

        try:
            resp = requests.get(url, headers=self.config.HEADERS, timeout=30, verify=False)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if exc.response.status_code == 404:
                logger.warning(f"{ticker} introuvable (404)")
            else:
                logger.error(f"HTTP error {ticker}: {exc}")
            return {}
        except requests.RequestException as exc:
            logger.error(f"Erreur réseau {ticker}: {exc}")
            return {}

        try:
            static = self.parser.extract_instrument_static_info(resp.text)
            session = self.parser.extract_session_data(resp.text)
            hist_vars = self.parser.extract_historical_variations(resp.text)
        except Exception as exc:
            logger.error(f"Erreur parsing {ticker}: {exc}")
            return {}

        data: Dict[str, Any] = {
            "ticker": ticker,
            "scraped_at": datetime.now(),
            "date": datetime.now().date(),
            **static,
            **session,
            **hist_vars,
        }

        self._save(data)
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        """Sauvegarde les données statiques et de séance dans Cassandra."""
        self.cassandra.save_instrument_static(data)
        self.cassandra.save_daily_price(data)
        logger.debug(f"Données sauvegardées pour {data.get('ticker')}")
