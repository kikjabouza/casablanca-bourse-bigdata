# src/scrapers/historical_data_scraper.py
import requests
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.utils.config import Config
from src.utils.logger import get_logger
from src.parsers.json_parser import JSONParser
from src.storage.cassandra_client import CassandraClient

logger = get_logger(__name__)

class HistoricalDataScraper:
    """Scraper pour les données historiques via l'API JSON"""
    
    def __init__(self):
        self.config = Config()
        self.parser = JSONParser()
        self.cassandra = CassandraClient()
    
    def get_instrument_id(self, ticker: str) -> Optional[int]:
        """ Obtient l'ID numérique via le JSON Next.js (plus fiable)"""
        
        url = f"https://www.casablanca-bourse.com/_next/data/k6VYoXBS432b__PEHJ2s2/fr/live-market/instruments/{ticker}.json"
        params = {"slug": ["fr", "live-market", "instruments", ticker]}
        
        try:
            response = requests.get(url, params=params, headers=self.config.HEADERS, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            
            # Parcourir les paragraphes pour trouver l'ID
            paragraphs = data.get("pageProps", {}).get("node", {}).get("field_vactory_paragraphs", [])
            for paragraph in paragraphs:
                component = paragraph.get("field_vactory_component", {})
                if component.get("widget_id") == "bourse_instrument:instrument-info":
                    widget_data = json.loads(component.get("widget_data", "{}"))
                    for comp in widget_data.get("components", []):
                        collection = comp.get("collection", {})
                        for item in collection.get("data", {}).get("data", []):
                            if item.get("type") == "instrument":
                                instrument_id = item.get("attributes", {}).get("drupal_internal__id")
                                if instrument_id:
                                    return instrument_id
            
            logger.warning(f"ID non trouvé pour {ticker}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'ID pour {ticker}: {e}")
            return None
    
    def scrape_historical_data(self, ticker: str, start_date: str = None) -> List[Dict[str, Any]]:
        """
        Scrape toutes les données historiques pour un instrument
        """
        instrument_id = self.get_instrument_id(ticker)
        if not instrument_id:
            logger.error(f"Impossible de trouver l'ID pour {ticker}")
            return []
        
        if not start_date:
            start_date = self.config.DEFAULT_START_DATE
        
        all_records = []
        offset = 0
        limit = self.config.DEFAULT_LIMIT
        
        while True:
            params = {
                "fields[instrument_history]": "drupal_internal__id,coursCourant,cumulVolumeEchange,created,lowPrice,highPrice,openingPrice,closingPrice,ratioConsolide",
                "sort[date-seance][path]": "created",
                "sort[date-seance][direction]": "ASC",
                "filter[instrument][condition][path]": "symbol.meta.drupal_internal__target_id",
                "filter[instrument][condition][value]": instrument_id,
                "filter[instrument][condition][operator]": "=",
                "filter[filter-date-start-vh-select][condition][path]": "field_seance_date",
                "filter[filter-date-start-vh-select][condition][operator]": ">=",
                "filter[filter-date-start-vh-select][condition][value]": start_date,
                "page[offset]": offset,
                "page[limit]": limit
            }
            
            try:
                response = requests.get(
                    self.config.get_instrument_api_url(instrument_id),
                    params=params,
                    headers=self.config.API_HEADERS,
                    timeout=30,
                    verify=False
                )
                response.raise_for_status()
                
                data = response.json()
                records = self.parser.parse_instrument_history(data, ticker)
                
                if not records:
                    break
                
                all_records.extend(records)
                logger.info(f"{ticker}: Récupéré {len(records)} jours (total: {len(all_records)})")
                
                # Vérifier si on a tout récupéré
                pagination = self.parser.extract_pagination_info(data)
                if offset + limit >= pagination.get('total_count', 0):
                    break
                
                offset += limit
                time.sleep(self.config.REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Erreur lors du scraping de l'historique pour {ticker}: {e}")
                break
        
        # Sauvegarder dans Cassandra
        if all_records:
            self._save_historical_data(all_records)
        
        return all_records
    
    def _save_historical_data(self, records: List[Dict[str, Any]]):
        """
        Sauvegarde les données historiques dans Cassandra
        """
        query = """
        INSERT INTO historical_prices (
            ticker, date, open_price, high_price, low_price,
            close_price, volume, adjusted_close, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))
        """
        
        for record in records:
            # Appliquer le ratio de consolidation pour ajuster les prix
            ratio = record.get('ratio', 1.0)
            adjusted_close = record['close_price'] / ratio if record['close_price'] else None
            
            self.cassandra.execute(query, (
                record['ticker'],
                record['date'],
                record['open_price'],
                record['high_price'],
                record['low_price'],
                record['close_price'],
                record['volume'],
                adjusted_close
            ))
        
        logger.info(f"Sauvegardé {len(records)} enregistrements historiques")