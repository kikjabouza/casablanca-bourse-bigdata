# src/scrapers/market_overview_scraper.py
"""
Scraper pour la page overview (indices, stats, top variations, futures).
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
    """Scraper pour les données globales du marché (exécution quotidienne)."""

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

    @retry(max_attempts=3, delay=2)
    def scrape_market_overview(self, enrich_top_movers: bool = False) -> Dict[str, Any]:
        """Scrape la page overview et retourne toutes les données."""
        try:
            logger.info(f"Scraping du market overview depuis {self.config.OVERVIEW_URL}")
            session = self.config.get_session()
            response = requests.get(
                self.config.OVERVIEW_URL,
                headers=self.config.HEADERS,
                timeout=30,
                verify=False,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

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

            if not market_data.get("futures"):
                market_data["futures"] = self._fetch_futures_from_terme_listing(session)

            if self.cassandra is not None:
                self._save_market_data(market_data)

            masi_value = market_data["indices"].get("MASI", {}).get("value")
            logger.info(
                f"Overview scrapé: {len(market_data['indices'])} indices, "
                f"{len(market_data['top_gainers'])} hausses, "
                f"{len(market_data['top_losers'])} baisses, MASI={masi_value}"
            )
            return market_data

        except Exception as exc:
            logger.error(f"Erreur lors du scraping du market overview: {exc}")
            return {}

    def _fetch_overview_widget_data(self, session: requests.Session) -> Dict[str, Any]:
        """Récupère les métadonnées embarquées dans le JSON Next.js."""
        try:
            response = session.get(
                self.config.get_overview_next_data_url(),
                timeout=30,
                verify=False,
            )
            response.raise_for_status()
            page_props = response.json().get("pageProps", {})
            paragraphs = page_props.get("node", {}).get("field_vactory_paragraphs", [])

            for paragraph in paragraphs:
                component = paragraph.get("field_vactory_component", {})
                if component.get("widget_id") == "bourse_data_listing:marches-overview":
                    return json.loads(component.get("widget_data", "{}"))
        except Exception as exc:
            logger.warning(f"Impossible de récupérer le widget overview: {exc}")
        return {}

    def _enrich_from_widget(
        self,
        market_data: Dict[str, Any],
        widget_data: Dict[str, Any],
        session: requests.Session,
    ) -> None:
        if not widget_data:
            return

        components = widget_data.get("components", [])
        if not components:
            return

        component = components[0]
        stats = market_data.setdefault("market_stats", {})

        volume_value = component.get("volume", {}).get("volume")
        cap_value = component.get("capitalisation", {}).get("value")
        if volume_value and not stats.get("global_volume"):
            stats["global_volume"] = safe_float(volume_value, 0.0)
        if cap_value and not stats.get("market_cap"):
            stats["market_cap"] = safe_float(cap_value, 0.0)

        collection = component.get("collection", {}).get("data", {}).get("data", [])
        if collection and "MASI" not in market_data["indices"]:
            latest = max(
                collection,
                key=lambda item: item.get("attributes", {}).get("transactTime", ""),
            )
            attrs = latest.get("attributes", {})
            market_data["indices"]["MASI"] = {
                "value": safe_float(attrs.get("indexValue"), 0.0),
                "variation": 0.0,
                "annual_variation": 0.0,
            }

    def _fill_missing_indices(
        self,
        market_data: Dict[str, Any],
        session: requests.Session,
    ) -> None:
        expected = ["MASI", "MASI20", "MASI_ESG"]
        missing = [name for name in expected if name not in market_data["indices"]]
        if not missing:
            return

        for display_name, taxonomy_id in self.config.INDEX_TAXONOMY_IDS.items():
            normalized = self._normalize_index_name(display_name)
            if normalized not in missing:
                continue

            index_data = self._fetch_index_card(session, taxonomy_id, display_name)
            if index_data:
                market_data["indices"][normalized] = index_data

    def _fetch_index_card(
        self,
        session: requests.Session,
        taxonomy_id: int,
        display_name: str,
    ) -> Optional[Dict[str, float]]:
        slug_map = self.INDEX_PAGE_SLUGS
        slug = slug_map.get(display_name)
        if not slug:
            return None

        url = f"{self.config.BASE_URL}/fr/live-market/indices/{slug}"
        try:
            response = session.get(url, timeout=30, verify=False)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            blocks = soup.find_all(
                "div",
                class_=lambda value: value and "bg-gray-800" in value if value else False,
            )
            for block in blocks:
                text = block.get_text(" ", strip=True)
                if display_name.replace(" ", "") not in text.replace(" ", "") and display_name not in text:
                    continue

                value_tag = block.find("span", attrs={"dir": "ltr"})
                if not value_tag:
                    continue

                value = self._parse_french_float(value_tag.get_text(strip=True))
                variations = self._extract_variations_from_block(block)
                return {
                    "value": value or 0.0,
                    "variation": variations[0] if variations else 0.0,
                    "annual_variation": variations[1] if len(variations) > 1 else 0.0,
                }

            return self._fetch_index_from_next_data(session, slug, display_name)
        except Exception as exc:
            logger.debug(f"Index {display_name} non récupéré via HTML: {exc}")
            return None

    def _fetch_index_from_next_data(
        self,
        session: requests.Session,
        slug: str,
        display_name: str,
    ) -> Optional[Dict[str, float]]:
        url = (
            f"{self.config.BASE_URL}/_next/data/{self.config.NEXT_BUILD_ID}/"
            f"fr/live-market/indices/{slug}.json"
        )
        try:
            response = session.get(url, timeout=30, verify=False)
            if response.status_code != 200:
                return None

            paragraphs = response.json().get("pageProps", {}).get("node", {}).get(
                "field_vactory_paragraphs", []
            )
            for paragraph in paragraphs:
                component = paragraph.get("field_vactory_component", {})
                widget_data = component.get("widget_data")
                if not widget_data:
                    continue

                payload = json.loads(widget_data)
                serialized = json.dumps(payload)
                values = re.findall(r'"indexValue"\s*:\s*"([\d.]+)"', serialized)
                if not values:
                    continue

                return {
                    "value": safe_float(values[-1], 0.0),
                    "variation": 0.0,
                    "annual_variation": 0.0,
                }
        except Exception as exc:
            logger.debug(f"Index {display_name} non récupéré via Next.js: {exc}")
        return None

    def _fill_missing_top_movers(
        self,
        market_data: Dict[str, Any],
        session: requests.Session,
        enrich: bool = False,
    ) -> None:
        gainers = market_data.get("top_gainers", [])
        losers = market_data.get("top_losers", [])

        if enrich and len(gainers) < 5:
            api_gainers = self._fetch_top_movers_from_api(
                session, self.TOP_MOVERS_HIGH_QUERY, positive=True
            )
            if api_gainers:
                market_data["top_gainers"] = api_gainers[:5]
        elif not gainers:
            api_gainers = self._fetch_top_movers_from_api(
                session, self.TOP_MOVERS_HIGH_QUERY, positive=True
            )
            if api_gainers:
                market_data["top_gainers"] = api_gainers[:5]

        if enrich and len(losers) < 5:
            api_losers = self._fetch_top_movers_from_api(
                session, self.TOP_MOVERS_LOW_QUERY, positive=False
            )
            if api_losers:
                market_data["top_losers"] = api_losers[:5]
        elif not losers:
            api_losers = self._fetch_top_movers_from_api(
                session, self.TOP_MOVERS_LOW_QUERY, positive=False
            )
            if api_losers:
                market_data["top_losers"] = api_losers[:5]

    def _fetch_top_movers_from_api(
        self,
        session: requests.Session,
        query_params: Dict[str, Any],
        *,
        positive: bool = True,
    ) -> List[Dict[str, Any]]:
        params = {
            **query_params,
            "include": "symbol",
            "fields[market_watch]": "difference,variationPercent,varVeille,coursCourant,coursCloture,code,symbol",
        }
        try:
            response = session.get(
                self.config.get_market_watch_url(),
                params=params,
                headers=self.config.API_HEADERS,
                timeout=30,
                verify=False,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.warning(f"API top movers indisponible: {exc}")
            return []

        included = {
            item["id"]: item.get("attributes", {})
            for item in payload.get("included", [])
            if item.get("type") == "instrument"
        }

        movers: List[Dict[str, Any]] = []
        for item in payload.get("data", []):
            attrs = item.get("attributes", {})
            symbol_rel = item.get("relationships", {}).get("symbol", {}).get("data", {})
            instrument = included.get(symbol_rel.get("id"), {})

            ticker = (
                instrument.get("field_code")
                or instrument.get("label")
                or (attrs.get("code", "").split("-")[0] if attrs.get("code") else "")
            )
            company_name = instrument.get("name") or instrument.get("label") or ticker

            price = safe_float(
                attrs.get("coursCourant") or attrs.get("coursCloture") or attrs.get("lastTradedPrice"),
                0.0,
            )
            difference = safe_float(attrs.get("difference"), 0.0)
            variation = safe_float(attrs.get("variationPercent") or attrs.get("varVeille"), 0.0)

            if not ticker:
                continue

            movers.append(
                {
                    "ticker": ticker,
                    "name": company_name,
                    "price": price or 0.0,
                    "difference": difference or 0.0,
                    "variation": variation or 0.0,
                }
            )

        key = "variation"
        movers.sort(key=lambda row: row.get(key, 0.0), reverse=positive)

        if any (mover.get("variation") for mover in movers):
            if positive:
                movers = [mover for mover in movers if mover.get("variation", 0) >= 0]
            else:
                movers = [mover for mover in movers if mover.get("variation", 0) <= 0]
                movers.sort(key=lambda row: row.get("variation", 0.0))

        return movers[:5]

    def _extract_indices(self, soup: BeautifulSoup) -> Dict[str, Dict[str, float]]:
        indices: Dict[str, Dict[str, float]] = {}

        indices_section = soup.find("h3", string=lambda text: text and "Indices" in text if text else False)
        search_root = indices_section.find_next("div", class_="grid") if indices_section else soup

        index_blocks = []
        if search_root:
            index_blocks.extend(
                search_root.find_all(
                    "div",
                    class_=lambda value: value and "bg-gray-800" in value if value else False,
                )
            )

        if not index_blocks:
            index_blocks = soup.find_all(
                "div",
                class_=lambda value: value and "bg-gray-800" in value if value else False,
            )

        for block in index_blocks:
            name_tag = block.find("a", href=lambda href: href and "/fr/live-market/indices/" in href if href else False)
            if not name_tag:
                heading = block.find(["h3", "h4", "p", "span"])
                if not heading:
                    continue
                raw_name = heading.get_text(strip=True)
                if raw_name.lower() in {"volume global", "capitalisation"}:
                    continue
                name = self._normalize_index_name(raw_name)
            else:
                name = self._normalize_index_name(name_tag.get_text(strip=True))

            value_tag = block.find("span", attrs={"dir": "ltr"})
            if not value_tag:
                continue

            value = self._parse_french_float(value_tag.get_text(strip=True))
            if value is None:
                continue

            variations = self._extract_variations_from_block(block)
            indices[name] = {
                "value": value,
                "variation": variations[0] if variations else 0.0,
                "annual_variation": variations[1] if len(variations) > 1 else 0.0,
            }

        logger.info(f"Indices extraits depuis HTML: {list(indices.keys())}")
        return indices

    def _extract_market_stats(self, soup: BeautifulSoup) -> Dict[str, float]:
        stats: Dict[str, float] = {}

        volume_elem = soup.find("p", string=lambda text: text and "Volume global" in text if text else False)
        if volume_elem:
            parent = volume_elem.find_parent("div", class_=lambda value: value and "bg-gray-800" in value if value else False)
            if parent:
                value_tag = parent.find("span", attrs={"dir": "ltr"})
                if value_tag:
                    stats["global_volume"] = self._parse_french_float(
                        value_tag.get_text(strip=True).replace("MAD", ""),
                        integer_style=True,
                    ) or 0.0

        cap_elem = soup.find("p", string=lambda text: text and "Capitalisation" in text if text else False)
        if cap_elem:
            parent = cap_elem.find_parent("div", class_=lambda value: value and "bg-gray-800" in value if value else False)
            if parent:
                value_tag = parent.find("span", attrs={"dir": "ltr"})
                if value_tag:
                    stats["market_cap"] = self._parse_french_float(
                        value_tag.get_text(strip=True).replace("MAD", ""),
                        integer_style=True,
                    ) or 0.0

        return stats

    def _extract_futures(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        futures: List[Dict[str, Any]] = []

        future_blocks = soup.find_all(
            "div",
            class_=lambda value: value and "535665" in str(value) if value else False,
        )

        for block in future_blocks:
            name_tag = block.find("a")
            if not name_tag:
                name_text = block.get_text(" ", strip=True)
                if "FUTURE" not in name_text.upper():
                    continue
                name = name_text.split("  ")[0].strip()
            else:
                name = name_tag.get_text(strip=True)

            if not name or "FUTURE" not in name.upper():
                continue

            value_tag = block.find("p", class_=lambda value: value and "text-xs" in value and "md:text-2xl" in value if value else False)
            if not value_tag:
                value_tag = block.find("p", class_=lambda value: value and "font-bold" in value if value else False)
            if not value_tag:
                value_tag = block.find("span", attrs={"dir": "ltr"})

            value = 0.0
            if value_tag:
                value = self._parse_french_float(value_tag.get_text(strip=True)) or 0.0

            variation = 0.0
            var_tag = block.find(
                "p",
                class_=lambda value: value and ("text-success-500" in value or "text-error-500" in value) if value else False,
            )
            if var_tag:
                var_span = var_tag.find("span", attrs={"dir": "ltr"})
                raw_var = var_span.get_text(strip=True) if var_span else var_tag.get_text(strip=True)
                variation = self._parse_french_float(raw_var.replace("%", "")) or 0.0

            futures.append({"name": name, "value": value, "variation": variation})

        if not futures:
            futures = self._extract_futures_from_next_payload(soup)

        return futures

    def _extract_futures_from_next_payload(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return []

        try:
            payload = json.loads(script.string)
            serialized = json.dumps(payload)
        except json.JSONDecodeError:
            return []

        futures = []
        pattern = re.compile(
            r"MASI20 FUTURE\s+(JUI\d+|SEP\d+|DEC\d+|MAR\d+)[^\"]*?"
            r"\"indexValue\"\\s*:\\s*\"([\\d.]+)\".*?"
            r"\"indexVariation\"\\s*:\\s*\"([\\d.-]+)\"",
            re.IGNORECASE,
        )
        for match in pattern.finditer(serialized):
            futures.append(
                {
                    "name": f"MASI20 FUTURE {match.group(1).upper()}",
                    "value": safe_float(match.group(2), 0.0),
                    "variation": safe_float(match.group(3), 0.0),
                }
            )
        return futures

    def _fetch_futures_from_terme_listing(self, session: requests.Session) -> List[Dict[str, Any]]:
        """Récupère les contrats MASI20 FUTURE JUI26 / SEP26 depuis la page instruments-terme."""
        futures: List[Dict[str, Any]] = []
        target_codes = ("JUI26", "SEP26")

        try:
            response = session.get(
                f"{self.config.BASE_URL}/_next/data/{self.config.NEXT_BUILD_ID}/fr/instruments-terme.json",
                timeout=30,
                verify=False,
            )
            response.raise_for_status()
            paragraphs = response.json().get("pageProps", {}).get("node", {}).get(
                "field_vactory_paragraphs", []
            )

            for paragraph in paragraphs:
                component = paragraph.get("field_vactory_component", {})
                if component.get("widget_id") != "bourse_data_listing:derive-instrument-listing":
                    continue

                widget_data = json.loads(component.get("widget_data", "{}"))
                items = (
                    widget_data.get("components", [{}])[0]
                    .get("collection", {})
                    .get("data", {})
                    .get("data", [])
                )

                for item in items:
                    attrs = item.get("attributes", {})
                    name = attrs.get("libelleFR") or attrs.get("symbol", "")
                    if not any(code in name.upper() for code in target_codes):
                        continue

                    symbol = attrs.get("symbol")
                    value, variation = self._fetch_future_quote(session, symbol)
                    futures.append(
                        {
                            "name": name,
                            "value": value,
                            "variation": variation,
                        }
                    )
        except Exception as exc:
            logger.warning(f"Impossible de récupérer les futures MASI20: {exc}")

        return futures

    def _fetch_future_quote(
        self,
        session: requests.Session,
        symbol: Optional[str],
    ) -> tuple[float, float]:
        if not symbol:
            return 0.0, 0.0

        next_url = (
            f"{self.config.BASE_URL}/_next/data/{self.config.NEXT_BUILD_ID}/"
            f"fr/live-market/instruments-derives/{symbol}.json"
        )
        try:
            response = session.get(next_url, timeout=20, verify=False)
            if response.status_code == 200:
                serialized = response.text
                values = re.findall(r'"indexValue"\s*:\s*"([\d.]+)"', serialized)
                variations = re.findall(r'"indexVariation"\s*:\s*"([\d.-]+)"', serialized)
                if not values:
                    values = re.findall(r'"coursCourant"\s*:\s*"([\d.]+)"', serialized)
                if not variations:
                    variations = re.findall(r'"varVeille"\s*:\s*"([\d.-]+)"', serialized)
                if values:
                    return safe_float(values[-1], 0.0) or 0.0, safe_float(
                        variations[-1], 0.0
                    ) if variations else 0.0
        except Exception as exc:
            logger.debug(f"Cotation future {symbol} via Next.js indisponible: {exc}")

        page_url = f"{self.config.BASE_URL}/fr/live-market/instruments-derives/{symbol}"
        try:
            response = session.get(page_url, timeout=20, verify=False)
            if response.status_code != 200:
                return 0.0, 0.0
            soup = BeautifulSoup(response.text, "html.parser")
            value = 0.0
            variation = 0.0

            value_tag = soup.find("span", attrs={"dir": "ltr"})
            if value_tag:
                value = self._parse_french_float(value_tag.get_text(strip=True)) or 0.0

            variation_tags = soup.find_all(
                "p",
                class_=lambda val: val and ("text-success-500" in val or "text-error-500" in val) if val else False,
            )
            if variation_tags:
                raw_variation = variation_tags[0].get_text(strip=True).replace("%", "")
                variation = self._parse_french_float(raw_variation) or 0.0

            return value, variation
        except Exception as exc:
            logger.debug(f"Cotation future {symbol} via HTML indisponible: {exc}")

        return 0.0, 0.0

    def _extract_top_gainers(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        return self._extract_top_movers_table(soup, "Les 5 plus fortes hausses", positive=True)

    def _extract_top_losers(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        return self._extract_top_movers_table(soup, "Les 5 plus fortes baisses", positive=False)

    def _extract_top_movers_table(
        self,
        soup: BeautifulSoup,
        section_title: str,
        positive: bool,
    ) -> List[Dict[str, Any]]:
        movers: List[Dict[str, Any]] = []

        section = soup.find("p", string=lambda text: text and section_title in text if text else False)
        if not section:
            section = soup.find(string=lambda text: text and section_title in text if text else False)
            if section:
                section = section.find_parent(["div", "section", "p"])

        if not section:
            return movers

        table = section.find_next("table")
        if not table:
            return movers

        rows = table.find_all("tr")[1:]
        for row in rows[:5]:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            link = cells[0].find("a")
            if link:
                name = link.get_text(strip=True)
                href = link.get("href", "")
                ticker = href.split("/")[-1] if href else name.split("-")[0].strip()
            else:
                name = cells[0].get_text(strip=True)
                ticker = name.split("-")[0].strip()

            price = self._parse_french_float(cells[1].get_text(strip=True)) or 0.0
            difference = self._parse_french_float(cells[2].get_text(strip=True).replace("+", "")) or 0.0
            variation = self._parse_french_float(cells[3].get_text(strip=True).replace("+", "").replace("%", "")) or 0.0

            movers.append(
                {
                    "ticker": ticker,
                    "name": name,
                    "price": price,
                    "difference": difference,
                    "variation": variation,
                }
            )

        return movers

    def _extract_variations_from_block(self, block: BeautifulSoup) -> List[float]:
        variations: List[float] = []
        variation_tags = block.find_all(
            "p",
            class_=lambda value: value and ("text-success-500" in value or "text-error-500" in value) if value else False,
        )

        for tag in variation_tags:
            var_span = tag.find("span", attrs={"dir": "ltr"})
            raw_value = var_span.get_text(strip=True) if var_span else tag.get_text(strip=True)
            parsed = self._parse_french_float(raw_value.replace("%", ""))
            if parsed is not None:
                variations.append(parsed)

        return variations

    def _normalize_index_name(self, raw_name: str) -> str:
        cleaned = raw_name.strip()
        return self.INDEX_ALIASES.get(cleaned, cleaned.replace(" ", "_").upper())

    def _parse_french_float(self, value: str, integer_style: bool = False) -> Optional[float]:
        if not value:
            return None

        cleaned = (
            value.replace("\u00a0", "")
            .replace(" ", "")
            .replace("MAD", "")
            .replace("%", "")
            .replace("+", "")
            .strip()
        )

        if integer_style and "," not in cleaned and "." not in cleaned:
            return safe_float(cleaned)

        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", ".")

        return safe_float(cleaned)

    def _save_market_data(self, data: Dict[str, Any]) -> None:
        if self.cassandra is None:
            return

        if isinstance(data["date"], date):
            trade_date = data["date"]
        else:
            trade_date = date.fromisoformat(str(data["date"]))

        for index_name, index_data in data.get("indices", {}).items():
            query = """
            INSERT INTO daily_indices (index_name, date, value, variation, annual_variation, updated_at)
            VALUES (%s, %s, %s, %s, %s, toTimestamp(now()))
            """
            self.cassandra.execute(
                query,
                (
                    index_name,
                    trade_date,
                    index_data.get("value"),
                    index_data.get("variation"),
                    index_data.get("annual_variation"),
                ),
            )

        stats = data.get("market_stats", {})
        if stats:
            query = """
            INSERT INTO market_stats (date, global_volume, market_cap, updated_at)
            VALUES (%s, %s, %s, toTimestamp(now()))
            """
            self.cassandra.execute(
                query,
                (
                    trade_date,
                    stats.get("global_volume"),
                    stats.get("market_cap"),
                ),
            )

        for rank, gainer in enumerate(data.get("top_gainers", []), 1):
            query = """
            INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))
            """
            self.cassandra.execute(
                query,
                (
                    trade_date,
                    "up",
                    rank,
                    gainer.get("ticker"),
                    gainer.get("name"),
                    gainer.get("price"),
                    gainer.get("variation"),
                ),
            )

        for rank, loser in enumerate(data.get("top_losers", []), 1):
            query = """
            INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))
            """
            self.cassandra.execute(
                query,
                (
                    trade_date,
                    "down",
                    rank,
                    loser.get("ticker"),
                    loser.get("name"),
                    loser.get("price"),
                    loser.get("variation"),
                ),
            )

        logger.info(
            f"Sauvegardé: {len(data.get('indices', {}))} indices, "
            f"{len(data.get('top_gainers', []))} gainers, "
            f"{len(data.get('top_losers', []))} losers"
        )
