# src/parsers/json_parser.py
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from src.utils.logger import get_logger

logger = get_logger(__name__)

class JSONParser:
    """Parseur pour les réponses JSON des APIs"""
    
    @staticmethod
    def parse_instrument_history(api_response: Dict[str, Any], ticker: str) -> List[Dict[str, Any]]:
        """
        Parse la réponse de l'API instrument_history
        Retourne une liste d'enregistrements historiques
        """
        records = []
        data = api_response.get('data', [])
        
        for item in data:
            attrs = item.get('attributes', {})
            
            # Ne garder que les jours avec un prix de clôture
            closing_price = attrs.get('closingPrice')
            if closing_price is None:
                continue
            
            record = {
                'ticker': ticker,
                'date': attrs.get('created'),
                'close_price': float(closing_price) if closing_price else None,
                'open_price': float(attrs['openingPrice']) if attrs.get('openingPrice') else None,
                'high_price': float(attrs['highPrice']) if attrs.get('highPrice') else None,
                'low_price': float(attrs['lowPrice']) if attrs.get('lowPrice') else None,
                'volume': float(attrs['cumulVolumeEchange']) if attrs.get('cumulVolumeEchange') else None,
                'current_price': float(attrs['coursCourant']) if attrs.get('coursCourant') else None,
                'ratio': float(attrs['ratioConsolide']) if attrs.get('ratioConsolide') else 1.0
            }
            records.append(record)
        
        logger.debug(f"Parsé {len(records)} enregistrements historiques pour {ticker}")
        return records
    
    @staticmethod
    def extract_pagination_info(api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait les informations de pagination de la réponse API
        """
        meta = api_response.get('meta', {})
        links = api_response.get('links', {})
        
        return {
            'total_count': meta.get('count', 0),
            'first_page': links.get('first', {}).get('href'),
            'last_page': links.get('last', {}).get('href'),
            'prev_page': links.get('prev', {}).get('href'),
            'next_page': links.get('next', {}).get('href')
        }