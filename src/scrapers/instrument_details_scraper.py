# src/scrapers/instrument_details_scraper.py
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from src.utils.config import Config
from src.utils.logger import get_logger
from src.parsers.html_parser import HTMLParser
from src.storage.cassandra_client import CassandraClient

logger = get_logger(__name__)

class InstrumentDetailsScraper:
    """Scraper pour les détails statiques et dynamiques d'un instrument"""
    
    def __init__(self):
        self.config = Config()
        self.parser = HTMLParser()
        self.cassandra = CassandraClient()
    
    def scrape_instrument(self, ticker: str) -> Dict[str, Any]:
        """
        Scrape toutes les informations pour un instrument donné
        """
        url = f"{self.config.INSTRUMENT_BASE_URL}/{ticker}"
        logger.info(f"Scraping de l'instrument {ticker} depuis {url}")
        
        try:
            response = requests.get(url, headers=self.config.HEADERS, timeout=30, verify=False)
            response.raise_for_status()
            html_content = response.text
            
            # Extraire les différentes catégories de données
            try:
                static_info = self.parser.extract_instrument_static_info(html_content)
                session_data = self.parser.extract_session_data(html_content)
                historical_vars = self.parser.extract_historical_variations(html_content)
            except Exception as parse_error:
                logger.error(f"Erreur lors du parsing de {ticker}: {parse_error}")
                return {}
            
            # Combiner toutes les données
            instrument_data = {
                'ticker': ticker,
                'scraped_at': datetime.now(),
                **static_info,
                **session_data,
                **historical_vars
            }
            
            # Sauvegarder dans Cassandra
            self._save_to_cassandra(instrument_data)
            
            return instrument_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Instrument {ticker} non trouvé (404): {url}")
            else:
                logger.error(f"Erreur HTTP pour {ticker}: {e}")
            return {}
        except requests.RequestException as e:
            logger.error(f"Erreur réseau lors du scraping de {ticker}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Erreur inattendue lors du scraping de {ticker}: {e}")
            return {}
    
    def _save_to_cassandra(self, data: Dict[str, Any]):
        """
        Sauvegarde les données de l'instrument dans Cassandra
        """
        ticker = data.get('ticker')
        if not ticker:
            return
        
        # En mode test, sauvegarder en JSON
        if self.cassandra.test_mode:
            self.cassandra.save_instrument_json(ticker, data)
            return
        
        # Table des données statiques (une seule ligne par instrument)
        static_query = """
        INSERT INTO instruments_static (
            ticker, isin, sector, listing_date, shares_count,
            nominal_value, trading_cycle, currency, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))
        """
        self.cassandra.execute(static_query, (
            ticker,
            data.get('isin'),
            data.get('sector'),
            data.get('listing_date'),
            data.get('shares_count'),
            data.get('nominal_value'),
            data.get('trading_cycle'),
            data.get('currency')
        ))
        
        # Table des données de séance (une ligne par jour/instrument)
        session_query = """
        INSERT INTO daily_prices (
            ticker, date, open_price, high_price, low_price,
            close_price, volume, quantity, trades_count,
            market_cap, variation, var_ytd, scraped_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))
        """
        self.cassandra.execute(session_query, (
            ticker,
            datetime.now().date(),
            data.get('opening_price'),
            data.get('high_price'),
            data.get('low_price'),
            data.get('current_price'),
            data.get('volume'),
            data.get('quantity'),
            data.get('trades_count'),
            data.get('market_cap'),
            data.get('variation'),
            data.get('var_ytd')
        ))
        
        logger.info(f"Sauvegardé les données pour {ticker}")