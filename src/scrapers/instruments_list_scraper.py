import requests
import urllib3
from typing import Dict, List

from src.parsers.html_parser import HTMLParser
from src.storage.cassandra_client import CassandraClient
from src.utils.config import Config
from src.utils.logger import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


class InstrumentsListScraper:
    """Scrape la liste complète des instruments cotés (via API JSON ou HTML)."""

    def __init__(self):
        self.config = Config()
        self.parser = HTMLParser()
        self.cassandra = CassandraClient()

    def scrape_instruments_list(self) -> List[Dict[str, str]]:
        """
        Retourne la liste complète des instruments: [{"ticker", "name", "url"}, ...].
        Tente d'abord l'API JSON paginée, puis parse le HTML en fallback.
        Sauvegarde dans Cassandra (no-op si mode stub).
        """
        instruments = self._scrape_from_api()
        if not instruments:
            logger.info("API échouée, fallback vers HTML")
            instruments = self._scrape_from_html()

        logger.info(f"{len(instruments)} instruments récupérés")

        for inst in instruments:
            self.cassandra.save_instrument(inst)

        return instruments

    def _scrape_from_api(self) -> List[Dict[str, str]]:
        """Récupère la liste via l'API JSON paginée."""
        instruments_map: Dict[str, Dict] = {}
        offset = 0
        limit = self.config.DEFAULT_LIMIT
        total_count = None

        try:
            while True:
                url = self.config.get_instruments_api_url(offset=offset, limit=limit)
                resp = requests.get(
                    url, headers=self.config.API_HEADERS, timeout=30, verify=False
                )
                if resp.status_code != 200:
                    break

                data = resp.json()
                items = data.get("data", [])
                if total_count is None:
                    total_count = data.get("meta", {}).get("count", len(items))

                for item in items:
                    attrs = item.get("attributes", {}) or {}
                    ticker = attrs.get("symbol") or attrs.get("codeInstrumentBourse", "")
                    if not ticker:
                        continue
                    name = (
                        attrs.get("libelleFR")
                        or attrs.get("libelleEN")
                        or attrs.get("libelleAR")
                        or ticker
                    )
                    url_path = (
                        attrs.get("instrument_url")
                        or f"/fr/live-market/instruments/{ticker}"
                    )
                    instruments_map[ticker] = {"ticker": ticker, "name": name, "url": url_path}

                if not items or total_count is None or offset + limit >= total_count:
                    break
                offset += limit

        except Exception as exc:
            logger.debug(f"API instruments échouée: {exc}")

        return list(instruments_map.values())

    def _scrape_from_html(self) -> List[Dict[str, str]]:
        """Fallback: parse la page overview HTML."""
        try:
            resp = requests.get(
                self.config.OVERVIEW_URL,
                headers=self.config.HEADERS,
                timeout=30,
                verify=False,
            )
            resp.raise_for_status()
            return self.parser.extract_instruments_list(resp.text)
        except Exception as exc:
            logger.error(f"Scraping HTML instruments échoué: {exc}")
            return []
