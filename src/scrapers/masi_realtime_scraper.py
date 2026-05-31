# src/scrapers/masi_realtime_scraper.py
"""
Scraper pour les données MASI en TEMPS RÉEL (à exécuter toutes les 2 minutes)
"""

import requests
from datetime import datetime
from typing import Dict, Any, Optional
from src.utils.config import Config
from src.utils.logger import get_logger
from src.storage.cassandra_client import CassandraClient

logger = get_logger(__name__)

class MASIRealtimeScraper:
    """Scraper pour le MASI en quasi-temps réel (toutes les 2 minutes)"""
    
    def __init__(self):
        self.config = Config()
        self.cassandra = CassandraClient()
        self.indices = ['MASI', 'MASI20', 'MASI_ESG']  # Indices à suivre
    
    def scrape_all_indices(self) -> Dict[str, Any]:
        """
        Scrape tous les indices en temps réel
        À exécuter toutes les 2 minutes pendant la séance
        """
        results = {}
        
        for index_name in self.indices:
            point = self.scrape_single_index(index_name)
            if point:
                results[index_name] = point
                self._save_intraday_point(point)
        
        logger.debug(f"Points MASI scrapés: {len(results)}")
        return results
    
    def scrape_single_index(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Scrape un seul indice (dernier point disponible)
        """
        url = "https://www.casablanca-bourse.com/api/proxy/fr/api/bourse_data/index_watch"
        
        params = {
            "fields[index_watch]": "indexValue,transactTime",
            "filter[index][condition][path]": "indexCode.field_code",
            "filter[index][condition][operator]": "=",
            "filter[index][condition][value]": index_name,
            "page[limit]": 1,  # Dernier point seulement
            "sort[transactTime][direction]": "DESC"
        }
        
        try:
            response = requests.get(
                url, 
                params=params, 
                headers=self.config.API_HEADERS,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                attrs = data['data'][0]['attributes']
                
                return {
                    'index_name': index_name,
                    'value': float(attrs.get('indexValue', 0)),
                    'timestamp': attrs.get('transactTime'),
                    'scraped_at': datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur scraping {index_name}: {e}")
            return None
    
    def _save_intraday_point(self, point: Dict[str, Any]):
        """
        Sauvegarde un point intraday dans Cassandra
        Table: intraday_indices
        """
        query = """
        INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at)
        VALUES (%s, %s, %s, %s, toTimestamp(now()))
        """
        
        date = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00')).date()
        
        self.cassandra.execute(query, (
            point['index_name'],
            date,
            point['timestamp'],
            point['value']
        ))
    
    def get_latest_value(self, index_name: str = 'MASI') -> Optional[float]:
        """
        Récupère la dernière valeur connue d'un indice
        """
        query = """
        SELECT value FROM intraday_indices 
        WHERE index_name = %s 
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        result = self.cassandra.execute(query, (index_name,))
        return result[0]['value'] if result else None