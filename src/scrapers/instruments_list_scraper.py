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
        Tente de récupérer la liste via l'API JSON
        """
        try:
            # URL de l'API pour la liste des instruments
            api_url = "https://www.casablanca-bourse.com/api/proxy/fr/api/bourse_data/instrument_list"
            
            response = requests.get(
                api_url,
                headers=self.config.HEADERS,
                timeout=30,
                verify=False
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            instruments = []
            
            # Parser la réponse JSON
            if 'data' in data:
                for item in data['data']:
                    attributes = item.get('attributes', {})
                    ticker = attributes.get('field_code', '')
                    name = attributes.get('field_name', '')
                    
                    if ticker:
                        instruments.append({
                            'ticker': ticker,
                            'name': name or ticker,
                            'url': f'/fr/live-market/instruments/{ticker}'
                        })
            
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