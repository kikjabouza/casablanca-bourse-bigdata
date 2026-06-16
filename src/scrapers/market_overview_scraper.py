"""
Scraper pour la page overview du marché: indices, stats globales, top hausses/baisses.
Conçu pour être appelé toutes les 2 minutes par market_overview_flow.
"""
import json
import re
import urllib3
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from src.storage.cassandra_client import CassandraClient
from src.utils.config import Config
from src.utils.helpers import retry, safe_float
from src.utils.logger import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


class MarketOverviewScraper:
    """Scraper du marché global (indices, stats, top movers)."""

    INDEX_ALIASES = {
        "MASI 20": "MASI20",
        "MASI20": "MASI20",
        "MASI": "MASI",
        "MASI ESG": "MASI_ESG",
        "MASI_ESG": "MASI_ESG",
        "MSI20": "MASI20",
        "ESGI": "MASI_ESG",
    }
    INDEX_PAGE_SLUGS = {
        "MASI": "MASI",
        "MASI20": "MSI20",
        "MASI ESG": "ESGI",
    }
    TOP_MOVERS_HIGH_QUERY = {
        "mw_high[limit]": 5,
        "mw_high[type_marche]": 59,
        "mw_high[classes][25]": 25,
        "mw_high[ss_classes][38]": 38,
    }
    TOP_MOVERS_LOW_QUERY = {
        "mw_low[limit]": 5,
        "mw_low[type_marche]": 59,
        "mw_low[classes][25]": 25,
        "mw_low[ss_classes][38]": 38,
    }

    def __init__(self, save_to_cassandra: bool = True):
        self.config = Config()
        self.cassandra = CassandraClient() if save_to_cassandra else None

    @retry(max_attempts=3, delay=2.0)
    def scrape_market_overview(self, enrich_top_movers: bool = False) -> Dict[str, Any]:
        """
        Scrape la page overview et retourne toutes les données du marché.
        Si save_to_cassandra=True, sauvegarde automatiquement dans Cassandra.
        """
        try:
            session = self.config.get_session()
            resp = requests.get(
                self.config.OVERVIEW_URL,
                headers=self.config.HEADERS,
                timeout=30,
                verify=False,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            widget_data = self._fetch_overview_widget_data(session)

            market_data: Dict[str, Any] = {
                "scraped_at": datetime.now(),
                "date": date.today(),
                "indices": self._extract_indices(soup),
                "market_stats": self._extract_market_stats(soup),
                "futures": self._extract_futures(soup),
                "top_gainers": self._extract_top_gainers(soup),
                "top_losers": self._extract_top_losers(soup),
            }

            self._enrich_from_widget(market_data, widget_data, session)
            self._fill_missing_indices(market_data, session)
            self._fill_missing_top_movers(market_data, session, enrich=enrich_top_movers)

            if self.cassandra is not None:
                self._save_market_data(market_data)

            logger.info(
                f"Overview scraped: {len(market_data['indices'])} indices, "
                f"{len(market_data['top_gainers'])} hausses, "
                f"{len(market_data['top_losers'])} baisses"
            )
            return market_data

        except Exception as exc:
            logger.error(f"Erreur scraping market overview: {exc}")
            return {}

    # ─── Extraction depuis le HTML ────────────────────────────────────────────

    def _extract_indices(self, soup: BeautifulSoup) -> Dict[str, Dict[str, float]]:
        indices: Dict[str, Dict[str, float]] = {}
        blocks = soup.find_all(
            "div",
            class_=lambda v: v and "bg-gray-800" in v,
        )
        for block in blocks:
            name_tag = block.find(
                "a", href=lambda h: h and "/fr/live-market/indices/" in h
            )
            if name_tag:
                name = self._normalize_index_name(name_tag.get_text(strip=True))
            else:
                heading = block.find(["h3", "h4", "p", "span"])
                if not heading:
                    continue
                raw = heading.get_text(strip=True)
                if raw.lower() in {"volume global", "capitalisation"}:
                    continue
                name = self._normalize_index_name(raw)

            value_tag = block.find("span", attrs={"dir": "ltr"})
            if not value_tag:
                continue
            value = self._parse_float(value_tag.get_text(strip=True))
            if value is None:
                continue

            variations = self._extract_variations_from_block(block)
            indices[name] = {
                "value": value,
                "variation": variations[0] if variations else 0.0,
                "annual_variation": variations[1] if len(variations) > 1 else 0.0,
            }

        return indices

    def _extract_market_stats(self, soup: BeautifulSoup) -> Dict[str, float]:
        stats: Dict[str, float] = {}
        for label, key in [("Volume global", "global_volume"), ("Capitalisation", "market_cap")]:
            elem = soup.find("p", string=lambda t: t and label in t)
            if not elem:
                continue
            parent = elem.find_parent("div", class_=lambda v: v and "bg-gray-800" in v)
            if not parent:
                continue
            tag = parent.find("span", attrs={"dir": "ltr"})
            if tag:
                val = self._parse_float(tag.get_text(strip=True).replace("MAD", ""), integer_style=True)
                if val is not None:
                    stats[key] = val
        return stats

    def _extract_futures(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        futures: List[Dict[str, Any]] = []
        blocks = soup.find_all(
            "div",
            class_=lambda v: v and "535665" in str(v),
        )
        for block in blocks:
            name_tag = block.find("a")
            name = name_tag.get_text(strip=True) if name_tag else block.get_text(" ", strip=True).split("  ")[0].strip()
            if not name or "FUTURE" not in name.upper():
                continue
            value_tag = block.find("span", attrs={"dir": "ltr"})
            value = self._parse_float(value_tag.get_text(strip=True)) or 0.0 if value_tag else 0.0
            var_tag = block.find("p", class_=lambda v: v and ("text-success-500" in v or "text-error-500" in v))
            variation = 0.0
            if var_tag:
                span = var_tag.find("span", attrs={"dir": "ltr"})
                raw = span.get_text(strip=True) if span else var_tag.get_text(strip=True)
                variation = self._parse_float(raw.replace("%", "")) or 0.0
            futures.append({"name": name, "value": value, "variation": variation})
        return futures

    def _extract_top_gainers(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        return self._extract_top_movers_table(soup, "Les 5 plus fortes hausses", positive=True)

    def _extract_top_losers(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        return self._extract_top_movers_table(soup, "Les 5 plus fortes baisses", positive=False)

    def _extract_top_movers_table(
        self, soup: BeautifulSoup, title: str, positive: bool
    ) -> List[Dict[str, Any]]:
        movers: List[Dict[str, Any]] = []
        section = soup.find("p", string=lambda t: t and title in t)
        if not section:
            return movers
        table = section.find_next("table")
        if not table:
            return movers
        for row in table.find_all("tr")[1:6]:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            link = cells[0].find("a")
            if link:
                name = link.get_text(strip=True)
                ticker = link.get("href", "").split("/")[-1]
            else:
                name = cells[0].get_text(strip=True)
                ticker = name.split("-")[0].strip()
            price = self._parse_float(cells[1].get_text(strip=True)) or 0.0
            difference = self._parse_float(cells[2].get_text(strip=True).replace("+", "")) or 0.0
            variation = self._parse_float(cells[3].get_text(strip=True).replace("+", "").replace("%", "")) or 0.0
            movers.append({"ticker": ticker, "name": name, "price": price, "difference": difference, "variation": variation})
        return movers

    # ─── Enrichissement via API / Next.js ────────────────────────────────────

    def _fetch_overview_widget_data(self, session: requests.Session) -> Dict[str, Any]:
        try:
            resp = session.get(self.config.get_overview_next_data_url(), timeout=30, verify=False)
            resp.raise_for_status()
            paragraphs = resp.json().get("pageProps", {}).get("node", {}).get("field_vactory_paragraphs", [])
            for paragraph in paragraphs:
                component = paragraph.get("field_vactory_component", {})
                if component.get("widget_id") == "bourse_data_listing:marches-overview":
                    return json.loads(component.get("widget_data", "{}"))
        except Exception as exc:
            logger.debug(f"Widget overview indisponible: {exc}")
        return {}

    def _enrich_from_widget(
        self, market_data: Dict, widget_data: Dict, session: requests.Session
    ) -> None:
        if not widget_data:
            return
        components = widget_data.get("components", [])
        if not components:
            return
        comp = components[0]
        stats = market_data.setdefault("market_stats", {})
        volume_val = comp.get("volume", {}).get("volume")
        cap_val = comp.get("capitalisation", {}).get("value")
        if volume_val and not stats.get("global_volume"):
            stats["global_volume"] = safe_float(volume_val, 0.0)
        if cap_val and not stats.get("market_cap"):
            stats["market_cap"] = safe_float(cap_val, 0.0)

    def _fill_missing_indices(self, market_data: Dict, session: requests.Session) -> None:
        expected = ["MASI", "MASI20", "MASI_ESG"]
        missing = [n for n in expected if n not in market_data["indices"]]
        if not missing:
            return
        for display_name, slug in self.INDEX_PAGE_SLUGS.items():
            normalized = self._normalize_index_name(display_name)
            if normalized not in missing:
                continue
            url = f"{self.config.BASE_URL}/fr/live-market/indices/{slug}"
            try:
                resp = session.get(url, timeout=30, verify=False)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                value_tag = soup.find("span", attrs={"dir": "ltr"})
                if value_tag:
                    value = self._parse_float(value_tag.get_text(strip=True))
                    if value:
                        market_data["indices"][normalized] = {
                            "value": value, "variation": 0.0, "annual_variation": 0.0
                        }
            except Exception as exc:
                logger.debug(f"Index {display_name} indisponible: {exc}")

    def _fill_missing_top_movers(
        self, market_data: Dict, session: requests.Session, enrich: bool = False
    ) -> None:
        gainers = market_data.get("top_gainers", [])
        losers = market_data.get("top_losers", [])
        if enrich or not gainers:
            api_gainers = self._fetch_top_movers_from_api(session, self.TOP_MOVERS_HIGH_QUERY, positive=True)
            if api_gainers:
                market_data["top_gainers"] = api_gainers[:5]
        if enrich or not losers:
            api_losers = self._fetch_top_movers_from_api(session, self.TOP_MOVERS_LOW_QUERY, positive=False)
            if api_losers:
                market_data["top_losers"] = api_losers[:5]

    def _fetch_top_movers_from_api(
        self, session: requests.Session, query_params: Dict, *, positive: bool = True
    ) -> List[Dict[str, Any]]:
        params = {
            **query_params,
            "include": "symbol",
            "fields[market_watch]": "difference,variationPercent,varVeille,coursCourant,coursCloture,code,symbol",
        }
        try:
            resp = session.get(
                self.config.get_market_watch_url(),
                params=params,
                headers=self.config.API_HEADERS,
                timeout=30,
                verify=False,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.debug(f"API top movers indisponible: {exc}")
            return []

        included = {
            item["id"]: item.get("attributes", {})
            for item in payload.get("included", [])
            if item.get("type") == "instrument"
        }
        movers: List[Dict] = []
        for item in payload.get("data", []):
            attrs = item.get("attributes", {})
            symbol_rel = item.get("relationships", {}).get("symbol", {}).get("data", {})
            instrument = included.get(symbol_rel.get("id"), {})
            ticker = (
                instrument.get("field_code") or instrument.get("label")
                or (attrs.get("code", "").split("-")[0] if attrs.get("code") else "")
            )
            if not ticker:
                continue
            movers.append({
                "ticker": ticker,
                "name": instrument.get("name") or ticker,
                "price": safe_float(attrs.get("coursCourant") or attrs.get("coursCloture"), 0.0),
                "difference": safe_float(attrs.get("difference"), 0.0),
                "variation": safe_float(attrs.get("variationPercent") or attrs.get("varVeille"), 0.0),
            })
        movers.sort(key=lambda r: r.get("variation", 0.0), reverse=positive)
        return movers[:5]

    # ─── Sauvegarde Cassandra ─────────────────────────────────────────────────

    def _save_market_data(self, data: Dict[str, Any]) -> None:
        if self.cassandra is None:
            return
        trade_date = data["date"]

        for index_name, index_data in data.get("indices", {}).items():
            self.cassandra.save_daily_index(index_name, trade_date, index_data)

        stats = data.get("market_stats", {})
        if stats:
            self.cassandra.save_market_stats(trade_date, stats)

        for rank, gainer in enumerate(data.get("top_gainers", []), 1):
            self.cassandra.save_top_mover(trade_date, "up", rank, gainer)
        for rank, loser in enumerate(data.get("top_losers", []), 1):
            self.cassandra.save_top_mover(trade_date, "down", rank, loser)

    # ─── Utilitaires ─────────────────────────────────────────────────────────

    def _normalize_index_name(self, raw: str) -> str:
        cleaned = raw.strip()
        return self.INDEX_ALIASES.get(cleaned, cleaned.replace(" ", "_").upper())

    def _parse_float(self, value: str, integer_style: bool = False) -> Optional[float]:
        if not value:
            return None
        cleaned = (
            value.replace("\xa0", "").replace(" ", "")
            .replace("MAD", "").replace("%", "").replace("+", "").strip()
        )
        if not cleaned or cleaned == "-":
            return None
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", ".")
        return safe_float(cleaned)

    def _extract_variations_from_block(self, block: BeautifulSoup) -> List[float]:
        variations: List[float] = []
        tags = block.find_all(
            "p",
            class_=lambda v: v and ("text-success-500" in v or "text-error-500" in v),
        )
        for tag in tags:
            span = tag.find("span", attrs={"dir": "ltr"})
            raw = span.get_text(strip=True) if span else tag.get_text(strip=True)
            val = self._parse_float(raw.replace("%", ""))
            if val is not None:
                variations.append(val)
        return variations
