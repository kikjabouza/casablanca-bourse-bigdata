# src/parsers/html_parser.py
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import re
from src.utils.logger import get_logger

logger = get_logger(__name__)

class HTMLParser:
    """Parseur pour extraire les données des pages HTML"""
    
    @staticmethod
    def extract_instruments_list(html_content: str) -> List[Dict[str, str]]:
        """
        Extrait la liste des instruments depuis la page overview
        Retourne: [{"ticker": "AGM", "name": "AGMA", "url": "/fr/live-market/instruments/AGM"}, ...]
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        instruments = []
        
        # Méthode 1: Chercher dans le JavaScript (plus fiable car souvent présent)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'field_instrument_list' in script.string:
                # Extraire via regex la liste des instruments
                import json
                match = re.search(r'field_instrument_list\s*:\s*(\[.*?\])', script.string, re.DOTALL)
                if match:
                    try:
                        instrument_list = json.loads(match.group(1))
                        for item in instrument_list:
                            ticker = item.get('url', '').split('/')[-1]
                            instruments.append({
                                'ticker': ticker,
                                'name': item.get('title', ''),
                                'url': item.get('url', '')
                            })
                        logger.info(f"Extrait {len(instruments)} instruments depuis le JavaScript")
                        return instruments
                    except json.JSONDecodeError as e:
                        logger.error(f"Erreur de parsing JSON: {e}")
        
        # Méthode 2: Fallback - chercher dans les liens HTML
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if '/fr/live-market/instruments/' in href:
                ticker = href.split('/')[-1]
                name = link.get_text(strip=True)
                if ticker and ticker not in [i['ticker'] for i in instruments]:
                    instruments.append({
                        'ticker': ticker,
                        'name': name,
                        'url': href
                    })
        
        logger.info(f"Extrait {len(instruments)} instruments depuis les liens HTML")
        return instruments
    
    @staticmethod
    def extract_instrument_static_info(html_content: str) -> Dict[str, Any]:
        """
        Extrait les informations statiques d'un instrument
        Retourne: {
            'isin': 'MA0000011058',
            'ticker': 'MNG',
            'sector': 'Mines',
            'listing_date': '2000-07-11',
            'shares_count': 11864676,
            'nominal_value': 100.0,
            'trading_cycle': 'Groupe 1',
            'currency': 'Dirham marocain'
        }
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        info = {}
        
        # Chercher le tableau "Informations sur l'instrument"
        info_table = soup.find('h3', string=re.compile(r'Informations sur l\'instrument'))
        if info_table:
            table = info_table.find_next('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        key = th.get_text(strip=True).lower().replace(' ', '_')
                        value = td.get_text(strip=True)
                        
                        # Nettoyer les valeurs
                        if key == 'isin':
                            info['isin'] = value
                        elif key == 'ticker':
                            info['ticker'] = value
                        elif key == 'secteur':
                            info['sector'] = value
                        elif key == 'date_introduction':
                            info['listing_date'] = value
                        elif key == 'nombre_de_titres':
                            # Enlever les espaces et convertir en int
                            cleaned = value.replace(' ', '').replace('-', '').strip()
                            if cleaned and cleaned != '-':
                                try:
                                    info['shares_count'] = int(cleaned)
                                except ValueError:
                                    logger.debug(f"Skipping invalid shares_count: {value}")
                        elif key == 'valeur_nominale':
                            cleaned = value.replace(',', '.').replace('-', '').strip()
                            if cleaned and cleaned != '-':
                                try:
                                    info['nominal_value'] = float(cleaned)
                                except ValueError:
                                    logger.debug(f"Skipping invalid nominal_value: {value}")
                        elif key == 'cycle_de_négociation':
                            info['trading_cycle'] = value
                        elif key == 'devise_de_cotation':
                            info['currency'] = value
        
        return info
    
    @staticmethod
    def extract_session_data(html_content: str) -> Dict[str, Any]:
        """
        Extrait les données de la séance pour un instrument
        Retourne: {
            'current_price': 17405.0,
            'variation': 4.85,
            'opening_price': 17000.0,
            'high_price': 17600.0,
            'low_price': 16850.0,
            'prev_close': 16600.0,
            'market_cap': 206504685780.0,
            'volume': 88984967.0,
            'quantity': 5155,
            'trades_count': 322,
            'timestamp': datetime
        }
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        session_data = {}
        
        # Chercher le tableau "Données de la séance"
        data_table = soup.find('h3', string=re.compile(r'Données de la séance'))
        if data_table:
            table = data_table.find_next('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        key = th.get_text(strip=True).lower().replace(' ', '_')
                        value_str = td.get_text(strip=True).replace(' ', '').replace(',', '.')
                        
                        # Convertir en nombre si possible, ignorer '-'
                        try:
                            if value_str == '-' or not value_str:
                                value = None
                            elif '%' in value_str:
                                value = float(value_str.replace('%', ''))
                            else:
                                value = float(value_str)
                        except (ValueError, TypeError):
                            value = value_str
                        
                        if value is not None:
                            if key == 'cours_(mad)':
                                session_data['current_price'] = value
                            elif key == 'variation':
                                session_data['variation'] = value
                            elif key == 'ouverture':
                                session_data['opening_price'] = value
                            elif key == 'plus_haut':
                                session_data['high_price'] = value
                            elif key == 'plus_bas':
                                session_data['low_price'] = value
                            elif key == 'cours_de_clôture_veille':
                                session_data['prev_close'] = value
                            elif key == 'capitalisation':
                                session_data['market_cap'] = value
                            elif key == 'volume':
                                session_data['volume'] = value
                            elif key == 'quantité_échangée':
                                if isinstance(value, (int, float)):
                                    session_data['quantity'] = int(value)
                            elif key == 'nombre_de_transactions':
                                if isinstance(value, (int, float)):
                                    session_data['trades_count'] = int(value)
        
        return session_data
    
    @staticmethod
    def extract_historical_variations(html_content: str) -> Dict[str, float]:
        """
        Extrait les variations historiques (depuis début d'année, etc.)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        variations = {}
        
        # Chercher le tableau "Données historiques"
        hist_table = soup.find('h3', string=re.compile(r'Données historiques'))
        if hist_table:
            table = hist_table.find_next('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        key = th.get_text(strip=True)
                        value_str = td.get_text(strip=True).replace(' ', '').replace(',', '.')
                        
                        # Extraire l'année et la valeur
                        if 'Var depuis le début de l\'année' in key:
                            variations['var_ytd'] = float(value_str.replace('%', ''))
                        elif 'Var depuis début 2025' in key:
                            variations['var_2025'] = float(value_str.replace('%', ''))
                        elif 'Var depuis début 2023' in key:
                            variations['var_2023'] = float(value_str.replace('%', ''))
                        elif 'Var depuis début 2021' in key:
                            variations['var_2021'] = float(value_str.replace('%', ''))
        
        return variations