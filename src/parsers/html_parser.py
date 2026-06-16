import json
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from src.utils.logger import get_logger

logger = get_logger(__name__)


class HTMLParser:
    """Parseur pour extraire les données des pages HTML de casablanca-bourse.com."""

    @staticmethod
    def extract_instruments_list(html_content: str) -> List[Dict[str, str]]:
        """
        Extrait la liste des instruments depuis la page overview.
        Retourne: [{"ticker": "AGM", "name": "AGMA", "url": "..."}, ...]
        """
        soup = BeautifulSoup(html_content, "html.parser")
        instruments = []

        # Méthode 1: JSON embarqué (Next.js __NEXT_DATA__)
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                payload = json.loads(script.string)
                serialized = json.dumps(payload)
                links = re.findall(r'"/fr/live-market/instruments/([A-Z0-9]+)"', serialized)
                seen = set()
                for ticker in links:
                    if ticker not in seen:
                        seen.add(ticker)
                        instruments.append(
                            {"ticker": ticker, "name": ticker, "url": f"/fr/live-market/instruments/{ticker}"}
                        )
                if instruments:
                    logger.info(f"Extrait {len(instruments)} instruments depuis __NEXT_DATA__")
                    return instruments
            except Exception as exc:
                logger.debug(f"Parsing __NEXT_DATA__ échoué: {exc}")

        # Méthode 2: Liens HTML directs
        links = soup.find_all("a", href=True)
        seen = set()
        for link in links:
            href = link["href"]
            if "/fr/live-market/instruments/" in href:
                ticker = href.rstrip("/").split("/")[-1]
                if ticker and ticker not in seen and len(ticker) >= 2:
                    seen.add(ticker)
                    name = link.get_text(strip=True) or ticker
                    instruments.append({"ticker": ticker, "name": name, "url": href})

        logger.info(f"Extrait {len(instruments)} instruments depuis les liens HTML")
        return instruments

    @staticmethod
    def extract_instrument_static_info(html_content: str) -> Dict[str, Any]:
        """
        Extrait les informations statiques d'un instrument (ISIN, secteur, etc.).
        """
        soup = BeautifulSoup(html_content, "html.parser")
        info: Dict[str, Any] = {}

        info_section = soup.find("h3", string=re.compile(r"Informations sur l.instrument", re.I))
        if not info_section:
            return info

        table = info_section.find_next("table")
        if not table:
            return info

        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not (th and td):
                continue

            key = th.get_text(strip=True).lower()
            value = td.get_text(strip=True)

            if "isin" in key:
                info["isin"] = value
            elif "secteur" in key:
                info["sector"] = value
            elif "introduction" in key or "admission" in key:
                info["listing_date"] = value
            elif "titres" in key or "actions" in key:
                cleaned = re.sub(r"[^\d]", "", value)
                if cleaned:
                    try:
                        info["shares_count"] = int(cleaned)
                    except ValueError:
                        pass
            elif "nominale" in key:
                cleaned = value.replace(",", ".").replace(" ", "").replace("\xa0", "")
                try:
                    info["nominal_value"] = float(cleaned)
                except ValueError:
                    pass
            elif "cycle" in key or "n" in key and "gociation" in key:
                info["trading_cycle"] = value
            elif "devise" in key or "cotation" in key:
                info["currency"] = value

        return info

    @staticmethod
    def extract_session_data(html_content: str) -> Dict[str, Any]:
        """
        Extrait les données de la séance pour un instrument (prix, volumes, variations).
        """
        soup = BeautifulSoup(html_content, "html.parser")
        session: Dict[str, Any] = {}

        data_section = soup.find("h3", string=re.compile(r"Donn.es de la s.ance", re.I))
        if not data_section:
            return session

        table = data_section.find_next("table")
        if not table:
            return session

        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not (th and td):
                continue

            key = th.get_text(strip=True).lower()
            raw = td.get_text(strip=True).replace("\xa0", "").replace(" ", "").replace(",", ".")

            def to_float(s: str):
                try:
                    return float(s.replace("%", "").replace("+", ""))
                except (ValueError, TypeError):
                    return None

            val = to_float(raw) if raw != "-" else None

            if val is not None:
                if "cours" in key and "mad" in key:
                    session["current_price"] = val
                elif "variation" in key and "%" in raw:
                    session["variation"] = val
                elif "ouverture" in key:
                    session["opening_price"] = val
                elif "haut" in key:
                    session["high_price"] = val
                elif "bas" in key:
                    session["low_price"] = val
                elif "veille" in key or "cl" in key and "ture" in key:
                    session["prev_close"] = val
                elif "capitalisation" in key:
                    session["market_cap"] = val
                elif "volume" in key:
                    session["volume"] = val
                elif "quantit" in key:
                    session["quantity"] = int(val)
                elif "transaction" in key or "nombre" in key:
                    session["trades_count"] = int(val)

        return session

    @staticmethod
    def extract_historical_variations(html_content: str) -> Dict[str, float]:
        """
        Extrait les variations historiques YTD depuis la page de l'instrument.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        variations: Dict[str, float] = {}

        hist_section = soup.find("h3", string=re.compile(r"Donn.es historiques", re.I))
        if not hist_section:
            return variations

        table = hist_section.find_next("table")
        if not table:
            return variations

        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not (th and td):
                continue

            key = th.get_text(strip=True)
            raw = td.get_text(strip=True).replace("\xa0", "").replace(" ", "").replace(",", ".")
            try:
                val = float(raw.replace("%", "").replace("+", ""))
            except (ValueError, TypeError):
                continue

            if "ann" in key.lower() or "ytd" in key.lower() or "d.but" in key.lower():
                variations["var_ytd"] = val

        return variations
