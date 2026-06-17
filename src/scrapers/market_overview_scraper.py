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
            widget_data = self._fetch_overview_widget_data(session, soup)

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

            # Source primaire des indices : API index_watch (fiable, indépendante du JS).
            # On écrase systématiquement les valeurs HTML (le site est 100% client-side,
            # requests.get() retourne des shells vides sans vraies données financières).
            api_indices = self._fetch_indices_from_api(session)
            market_data["indices"].update(api_indices)

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
                # Le site a 2 <a> par bloc : un overlay absolu (pas de texte, aria-label)
                # et un lien visible (avec texte). On préfère le texte, sinon aria-label.
                raw = name_tag.get_text(strip=True) or name_tag.get("aria-label", "")
                name = self._normalize_index_name(raw)
            else:
                heading = block.find(["h3", "h4", "p", "span"])
                if not heading:
                    continue
                raw = heading.get_text(strip=True)
                if raw.lower() in {"volume global", "capitalisation"}:
                    continue
                name = self._normalize_index_name(raw)

            if not name:
                continue

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

    def _fetch_overview_widget_data(
        self, session: requests.Session, soup: Optional[BeautifulSoup] = None
    ) -> Dict[str, Any]:
        # Source primaire : __NEXT_DATA__ déjà dans le HTML (pas de requête supplémentaire,
        # pas de dépendance au BUILD_ID).
        if soup is not None:
            try:
                script = soup.find("script", id="__NEXT_DATA__")
                if script and script.string:
                    next_data = json.loads(script.string)
                    # Mettre à jour le BUILD_ID en cache (évite de casser si le site déploie).
                    build_id = next_data.get("buildId")
                    if build_id:
                        self._build_id = build_id
                    paragraphs = (
                        next_data.get("props", {})
                        .get("pageProps", {})
                        .get("node", {})
                        .get("field_vactory_paragraphs", [])
                    )
                    for para in paragraphs:
                        comp = para.get("field_vactory_component", {})
                        if comp.get("widget_id") == "bourse_data_listing:marches-overview":
                            data = json.loads(comp.get("widget_data", "{}"))
                            if data:
                                logger.debug(
                                    f"Widget data (NEXT_DATA) keys: "
                                    f"{list(data.get('components', [{}])[0].keys()) if data.get('components') else data.keys()}"
                                )
                                return data
            except Exception as exc:
                logger.debug(f"__NEXT_DATA__ parsing failed: {exc}")

        # Fallback : requête HTTP vers l'API Next.js (nécessite un BUILD_ID valide).
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
        logger.info(f"Widget component keys: {list(comp.keys())}")

        stats = market_data.setdefault("market_stats", {})
        volume_val = comp.get("volume", {}).get("volume")
        cap_val = comp.get("capitalisation", {}).get("value")
        if volume_val and not stats.get("global_volume"):
            stats["global_volume"] = safe_float(volume_val, 0.0)
        if cap_val and not stats.get("market_cap"):
            stats["market_cap"] = safe_float(cap_val, 0.0)

        # Tenter d'extraire les indices depuis le widget (structure Vactory Factory).
        # Les clés possibles : "indices", "indice_details", "marche", etc.
        for key in ("indices", "indice_details", "index_data", "marche"):
            index_list = comp.get(key)
            if not isinstance(index_list, list):
                continue
            for entry in index_list:
                logger.debug(f"Widget index entry ({key}): {entry}")
                raw_name = (
                    entry.get("label") or entry.get("name")
                    or entry.get("code") or entry.get("libelle") or ""
                )
                raw_value = (
                    entry.get("value") or entry.get("cours")
                    or entry.get("cours_courant") or entry.get("current") or ""
                )
                raw_var = (
                    entry.get("variation") or entry.get("var")
                    or entry.get("variationPercent") or "0"
                )
                name = self._normalize_index_name(str(raw_name))
                if name not in ("MASI", "MASI20", "MASI_ESG"):
                    continue
                v = safe_float(str(raw_value).replace(",", ".").replace(" ", ""))
                if v and name not in market_data["indices"]:
                    market_data["indices"][name] = {
                        "value": v,
                        "variation": safe_float(str(raw_var).replace(",", ".").replace(" ", ""), 0.0),
                        "annual_variation": 0.0,
                    }
                    logger.info(f"Widget → {name} = {v}")

    def _fetch_indices_from_api(self, session: requests.Session) -> Dict[str, Dict[str, float]]:
        """
        Récupère MASI, MASI20, MASI_ESG depuis l'API index_watch.
        - indexValue       : valeur temps réel (pendant les heures de marché)
        - indexClotureValue: valeur de clôture (disponible même après la fermeture)
        Mappe par drupal_internal__target_id depuis la relation indexCode.
        """
        TID_TO_NAME = {512343: "MASI20", 512335: "MASI", 512320: "MASI_ESG"}
        indices: Dict[str, Dict[str, float]] = {}
        try:
            resp = session.get(
                f"{self.config.API_BASE_URL}/index_watch",
                params={"include": "indexCode"},
                headers=self.config.API_HEADERS,
                timeout=30,
                verify=False,
            )
            resp.raise_for_status()
            payload = resp.json()
            for item in payload.get("data", []):
                attrs = item.get("attributes", {})
                rel_data = (
                    item.get("relationships", {})
                    .get("indexCode", {})
                    .get("data", {})
                )
                tid = (
                    rel_data.get("meta", {}).get("drupal_internal__target_id")
                    if isinstance(rel_data, dict) else None
                )
                name = TID_TO_NAME.get(tid)
                if not name:
                    continue
                # Pendant les heures de marché : indexValue ; après clôture : indexClotureValue
                value = safe_float(attrs.get("indexValue")) or safe_float(attrs.get("indexClotureValue"))
                if value:
                    indices[name] = {
                        "value": value,
                        "variation": safe_float(attrs.get("varVeille"), 0.0),
                        "annual_variation": safe_float(attrs.get("varYear"), 0.0),
                    }
                    logger.info(f"index_watch API → {name} = {value}")
        except Exception as exc:
            logger.debug(f"index_watch API indisponible: {exc}")
        return indices

    def _fill_missing_indices(self, market_data: Dict, session: requests.Session) -> None:
        """
        Fallback : récupère les indices manquants depuis les pages _next/data individuelles.
        Widget "bourse_data_listing:index-graph-intraday" → collection_index.data.data[-1].indexValue
        (dernier tick intraday = valeur de clôture la plus récente).
        """
        expected = ["MASI", "MASI20", "MASI_ESG"]
        missing = [n for n in expected if n not in market_data["indices"]]
        if not missing:
            return
        logger.info(f"Indices manquants, fallback _next/data pages individuelles: {missing}")

        SLUG_MAP = {"MASI": "MASI", "MASI20": "MSI20", "MASI_ESG": "ESGI"}
        build_id = getattr(self, "_build_id", self.config.NEXT_BUILD_ID)

        for name in missing:
            slug = SLUG_MAP.get(name)
            if not slug:
                continue
            try:
                url = (
                    f"{self.config.BASE_URL}/_next/data/{build_id}"
                    f"/fr/live-market/indices/{slug}.json"
                )
                resp = session.get(url, timeout=30, verify=False)
                if resp.status_code != 200:
                    logger.warning(f"_next/data {slug} → HTTP {resp.status_code}")
                    continue
                paragraphs = (
                    resp.json().get("pageProps", {})
                    .get("node", {})
                    .get("field_vactory_paragraphs", [])
                )
                value = None
                for p in paragraphs:
                    comp = p.get("field_vactory_component", {})
                    if comp.get("widget_id") != "bourse_data_listing:index-graph-intraday":
                        continue
                    try:
                        wd = json.loads(comp.get("widget_data", "{}"))
                        coll_raw = wd.get("components", [{}])[0].get("collection_index", {})
                        coll = coll_raw if isinstance(coll_raw, dict) else json.loads(coll_raw)
                        items = coll.get("data", {}).get("data", [])
                        if items:
                            # L'ordre des items n'est pas garanti → trier par transactTime
                            # pour obtenir le tick le plus récent (valeur de clôture).
                            items_sorted = sorted(
                                items,
                                key=lambda x: x.get("attributes", {}).get("transactTime", ""),
                            )
                            last_attrs = items_sorted[-1].get("attributes", {})
                            v = safe_float(last_attrs.get("indexValue"))
                            if v and v > 100:
                                value = v
                                break
                    except Exception:
                        continue
                if value:
                    logger.info(f"_next/data fallback → {name} = {value}")
                    market_data["indices"][name] = {
                        "value": value, "variation": 0.0, "annual_variation": 0.0
                    }
                else:
                    logger.warning(f"Impossible d'extraire {name} depuis _next/data/{slug}.json")
            except Exception as exc:
                logger.debug(f"Fallback {name} indisponible: {exc}")

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
        """
        Retourne les top 5 gainers ou losers depuis l'API market_watch.

        Limites API :
        - L'endpoint retourne une watchlist fixe de ~26 instruments (pas le marché entier).
        - Les champs varVeille/difference sont uniquement disponibles pendant les heures
          de marché (09h00-15h30 Morocco / 08h00-14h30 UTC).
        - Après la clôture → retourne [] pour préserver les données existantes en Cassandra.
        """
        # Passer les brackets littéraux dans l'URL (pas via params= qui les encode %5B%5D)
        qs = "&".join(["include=symbol"] + [f"{k}={v}" for k, v in query_params.items()])
        url = f"{self.config.get_market_watch_url()}?{qs}"
        try:
            resp = session.get(url, headers=self.config.API_HEADERS, timeout=30, verify=False)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.debug(f"API top movers indisponible: {exc}")
            return []

        # Lookup ticker → nom complet (via included.libelleFR, matched par symbol)
        name_by_symbol: Dict[str, str] = {}
        for item in payload.get("included", []):
            if item.get("type") == "instrument":
                attrs = item.get("attributes", {})
                sym = attrs.get("symbol") or attrs.get("codeInstrumentBourse", "")
                if sym:
                    name_by_symbol[sym] = (
                        attrs.get("libelleFR") or attrs.get("libelleEN") or sym
                    )

        movers: List[Dict] = []
        for item in payload.get("data", []):
            attrs = item.get("attributes", {})
            code_raw = attrs.get("code", "")
            ticker = code_raw.split("-")[0] if "-" in code_raw else code_raw
            if not ticker:
                continue

            # varVeille = variation quotidienne % — uniquement renseigné pendant les heures de marché.
            # IMPORTANT : utiliser UNIQUEMENT varVeille, pas variationPercent (qui retourne 0 hors marché).
            # varVeille=None → marché fermé → on saute cet item pour éviter de stocker variation=0.
            var_veille_raw = attrs.get("varVeille")
            if var_veille_raw is None:
                continue
            variation = safe_float(var_veille_raw)
            if variation is None:
                continue

            price = safe_float(
                attrs.get("coursCourant") or attrs.get("lastTradedPrice")
                or attrs.get("coursCloture") or attrs.get("closingPrice"),
                0.0,
            )
            movers.append({
                "ticker": ticker,
                "name": name_by_symbol.get(ticker, ticker),
                "price": price,
                "difference": safe_float(attrs.get("difference"), 0.0),
                "variation": variation,
            })

        if not movers:
            logger.debug("top_movers: variation=None (hors heures de marché) → données Cassandra préservées")
            return []

        # Filtrer par signe : une hausse doit avoir variation > 0, une baisse < 0.
        # Évite de stocker des "hausses" à variation négative les jours très baissiers.
        if positive:
            movers = [m for m in movers if m.get("variation", 0.0) > 0]
        else:
            movers = [m for m in movers if m.get("variation", 0.0) < 0]

        if not movers:
            logger.debug(
                f"top_movers ({'up' if positive else 'down'}): aucun instrument avec variation "
                f"{'> 0' if positive else '< 0'} → données Cassandra préservées"
            )
            return []

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
            value.replace("\xa0", "").replace(" ", "").replace(" ", "")
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
