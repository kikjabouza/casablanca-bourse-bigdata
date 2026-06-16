import json
import time
import urllib3
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import requests

from src.parsers.json_parser import JSONParser
from src.storage.cassandra_client import CassandraClient
from src.utils.config import Config
from src.utils.logger import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


class HistoricalDataScraper:
    """
    Scrape les données historiques OHLC d'un instrument via l'API JSON.
    Deux modes d'utilisation:
      - Chargement initial : 1 an complet (appel depuis scripts/run_initial_load.py)
      - Mise à jour quotidienne : uniquement le dernier jour (via historical_flow)
    """

    def __init__(self):
        self.config = Config()
        self.parser = JSONParser()
        self.cassandra = CassandraClient()

    def get_instrument_id(self, ticker: str) -> Optional[int]:
        """Récupère l'ID numérique de l'instrument via le JSON Next.js."""
        url = (
            f"https://www.casablanca-bourse.com/_next/data/"
            f"{self.config.NEXT_BUILD_ID}/fr/live-market/instruments/{ticker}.json"
        )
        try:
            resp = requests.get(
                url, headers=self.config.HEADERS, timeout=30, verify=False
            )
            resp.raise_for_status()
            data = resp.json()

            paragraphs = (
                data.get("pageProps", {})
                    .get("node", {})
                    .get("field_vactory_paragraphs", [])
            )
            for paragraph in paragraphs:
                component = paragraph.get("field_vactory_component", {})
                if component.get("widget_id") == "bourse_instrument:instrument-info":
                    widget = json.loads(component.get("widget_data", "{}"))
                    for comp in widget.get("components", []):
                        for item in comp.get("collection", {}).get("data", {}).get("data", []):
                            if item.get("type") == "instrument":
                                inst_id = item.get("attributes", {}).get("drupal_internal__id")
                                if inst_id:
                                    logger.info(f"ID instrument {ticker}: {inst_id}")
                                    return inst_id
        except Exception as exc:
            logger.warning(f"Impossible de récupérer l'ID pour {ticker}: {exc}")
        return None

    def scrape_historical_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape toutes les données historiques pour un instrument entre start_date et end_date.

        Args:
            ticker: Symbole de l'instrument (ex: 'ATW')
            start_date: Date de début ISO (ex: '2024-06-15'). Défaut: 1 an en arrière.
            end_date: Date de fin ISO. Défaut: aujourd'hui.
        """
        if not start_date:
            start_date = (date.today() - timedelta(days=365)).isoformat()
        if not end_date:
            end_date = date.today().isoformat()

        instrument_id = self.get_instrument_id(ticker)
        if not instrument_id:
            logger.error(f"ID introuvable pour {ticker}, scraping annulé")
            return []

        logger.info(f"Scraping historique {ticker} du {start_date} au {end_date}")
        all_records: List[Dict] = []
        offset = 0
        limit = self.config.DEFAULT_LIMIT

        while True:
            params = {
                "fields[instrument_history]": (
                    "drupal_internal__id,coursCourant,cumulVolumeEchange,created,"
                    "lowPrice,highPrice,openingPrice,closingPrice,ratioConsolide"
                ),
                "sort[date-seance][path]": "created",
                "sort[date-seance][direction]": "ASC",
                "filter[instrument][condition][path]": "symbol.meta.drupal_internal__target_id",
                "filter[instrument][condition][value]": instrument_id,
                "filter[instrument][condition][operator]": "=",
                "filter[filter-date-start][condition][path]": "field_seance_date",
                "filter[filter-date-start][condition][operator]": ">=",
                "filter[filter-date-start][condition][value]": start_date,
                "filter[filter-date-end][condition][path]": "field_seance_date",
                "filter[filter-date-end][condition][operator]": "<=",
                "filter[filter-date-end][condition][value]": end_date,
                "page[offset]": offset,
                "page[limit]": limit,
            }

            try:
                resp = requests.get(
                    self.config.get_instrument_history_url(),
                    params=params,
                    headers=self.config.API_HEADERS,
                    timeout=30,
                    verify=False,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                logger.warning(f"Erreur API historique {ticker} (offset={offset}): {exc}")
                break

            records = self.parser.parse_instrument_history(data, ticker)
            if not records:
                break

            all_records.extend(records)
            logger.info(f"{ticker}: {len(all_records)} jours récupérés")

            pagination = self.parser.extract_pagination_info(data)
            if offset + limit >= pagination.get("total_count", 0):
                break

            offset += limit
            time.sleep(self.config.REQUEST_DELAY)

        # Sauvegarde dans Cassandra
        for record in all_records:
            self.cassandra.save_historical_price(record)

        logger.info(f"{ticker}: {len(all_records)} enregistrements sauvegardés")
        return all_records
