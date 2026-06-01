# src/scrapers/instruments_list_scraper.py
import requests
from typing import List, Dict
from src.utils.config import Config
from src.utils.logger import get_logger
from src.parsers.html_parser import HTMLParser
from src.storage.cassandra_client import CassandraClient

logger = get_logger(__name__)

class InstrumentsListScraper:
    """Scraper pour obtenir la liste de tous les instruments cotés"""
    
    def __init__(self):
        self.config = Config()
        self.parser = HTMLParser()
        self.cassandra = CassandraClient()
    
    def scrape_instruments_list(self) -> List[Dict[str, str]]:
        """
        Scrape la page overview pour obtenir la liste des instruments
        Utilise l'API JSON si disponible, sinon parse le HTML
        """
        try:
            # Méthode 1: Essayer l'API JSON
            instruments = self._scrape_from_api()
            if instruments:
                logger.info(f"✅ {len(instruments)} instruments trouvés via API")
                self._save_instruments_to_cassandra(instruments)
                return instruments
            
            # Méthode 2: Parser le HTML
            logger.info(f"Scraping de la liste des instruments depuis {self.config.OVERVIEW_URL}")
            response = requests.get(
                self.config.OVERVIEW_URL,
                headers=self.config.HEADERS,
                timeout=30,
                verify=False
            )
            response.raise_for_status()
            
            # Extraire la liste des instruments
            instruments = self.parser.extract_instruments_list(response.text)
            logger.info(f"✅ {len(instruments)} instruments trouvés via HTML")
            
            # Sauvegarder la liste des instruments
            self._save_instruments_to_cassandra(instruments)
            
            return instruments
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors du scraping de la liste des instruments: {e}")
            return []
    
    def _scrape_from_api(self) -> List[Dict[str, str]]:
        """
        Tente de récupérer la liste via l'API JSON paginée
        """
        try:
            instruments_map = {}
            offset = 0
            limit = 250
            total_count = None

            while True:
                api_url = self.config.get_instruments_api_url(offset=offset, limit=limit)
                response = requests.get(
                    api_url,
                    headers=self.config.API_HEADERS,
                    timeout=30,
                    verify=False
                )

                if response.status_code != 200:
                    logger.debug(f"Instrument API status {response.status_code} pour {api_url}")
                    break

                data = response.json()
                page_items = data.get('data', [])
                if total_count is None:
                    total_count = data.get('meta', {}).get('count', len(page_items))

                for item in page_items:
                    attributes = item.get('attributes', {}) or {}
                    ticker = attributes.get('symbol') or attributes.get('codeInstrumentBourse', '')
                    if not ticker:
                        continue

                    name = (
                        attributes.get('libelleFR') or
                        attributes.get('libelleEN') or
                        attributes.get('libelleAR') or
                        ticker
                    )

                    url = attributes.get('instrument_url') or f'/fr/live-market/instruments/{ticker}'
                    instruments_map[ticker] = {
                        'ticker': ticker,
                        'name': name,
                        'url': url
                    }

                if not page_items or total_count is None or offset + limit >= total_count:
                    break

                offset += limit

            instruments = list(instruments_map.values())
            return instruments

        except Exception as e:
            logger.debug(f"API scraping échoué: {e}")
            return []
    
    def _save_instruments_to_cassandra(self, instruments: List[Dict[str, str]]):
        """
        Sauvegarde la liste des instruments dans Cassandra
        """
        for instrument in instruments:
            query = """
            INSERT INTO instruments (ticker, name, url, updated_at)
            VALUES (%s, %s, %s, toTimestamp(now()))
            """
            self.cassandra.execute(query, (
                instrument['ticker'],
                instrument['name'],
                instrument['url']
            ))
        
        logger.info(f"Sauvegardé {len(instruments)} instruments dans Cassandra")