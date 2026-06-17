import os
from typing import Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration centralisée pour tous les scrapers et la stack."""

    # ─── URLs Bourse de Casablanca ────────────────────────────────────────────
    BASE_URL: str = os.getenv("BOURSE_BASE_URL", "https://www.casablanca-bourse.com")
    OVERVIEW_URL: str = f"{BASE_URL}/fr/live-market/overview"
    INSTRUMENT_BASE_URL: str = f"{BASE_URL}/fr/live-market/instruments"
    API_BASE_URL: str = f"{BASE_URL}/api/proxy/fr/api/bourse_data"
    NEXT_BUILD_ID: str = os.getenv("NEXT_BUILD_ID", "k6VYoXBS432b__PEHJ2s2")

    # ─── Headers HTTP ─────────────────────────────────────────────────────────
    HEADERS: Dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    API_HEADERS: Dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/vnd.api+json",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Referer": BASE_URL,
    }

    # ─── Cassandra ────────────────────────────────────────────────────────────
    CASSANDRA_HOST: str = os.getenv("CASSANDRA_HOST", "localhost")
    CASSANDRA_PORT: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    CASSANDRA_KEYSPACE: str = os.getenv("CASSANDRA_KEYSPACE", "bourse_data")
    # CASSANDRA_STUB=true désactive toutes les connexions DB (mode test sans infrastructure)
    CASSANDRA_STUB: bool = os.getenv("CASSANDRA_STUB", "false").lower() == "true"

    # ─── Trino ───────────────────────────────────────────────────────────────
    TRINO_HOST: str = os.getenv("TRINO_HOST", "localhost")
    TRINO_PORT: int = int(os.getenv("TRINO_PORT", "8080"))
    TRINO_CATALOG: str = "cassandra"
    TRINO_SCHEMA: str = os.getenv("CASSANDRA_KEYSPACE", "bourse_data")
    TRINO_USER: str = "admin"

    # ─── Prefect ─────────────────────────────────────────────────────────────
    PREFECT_API_URL: str = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")

    # ─── Paramètres de scraping ───────────────────────────────────────────────
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "0.5"))
    BULK_REQUEST_DELAY: float = float(os.getenv("BULK_REQUEST_DELAY", "1.0"))
    DEFAULT_LIMIT: int = 250
    MAX_OFFSET: int = 5000

    # ─── Instruments suivis pour détails + historique (10 instruments) ────────
    # Personnalisable via la variable d'env TRACKED_INSTRUMENTS (ex: "ATW,BCP,IAM,...")
    TRACKED_INSTRUMENTS: List[str] = [
        t.strip()
        for t in os.getenv(
            "TRACKED_INSTRUMENTS",
            "ATW,BCP,IAM,MNG,ADH,CIH,ALM,DHO,HPS,ATH"
        ).split(",")
        if t.strip()
    ]

    # ─── Indices du marché ────────────────────────────────────────────────────
    INDEX_TAXONOMY_IDS: Dict[str, int] = {
        "MASI20": 512343,
        "MASI": 512335,
        "MASI ESG": 512320,
    }

    ANOMALY_THRESHOLD: float = float(os.getenv("ANOMALY_THRESHOLD", "2.0"))

    @classmethod
    def get_session(cls) -> requests.Session:
        """Retourne une session HTTP réutilisable avec headers communs."""
        session = requests.Session()
        session.headers.update(cls.HEADERS)
        return session

    @classmethod
    def get_instruments_api_url(cls, offset: int = 0, limit: int = 250) -> str:
        return f"{cls.API_BASE_URL}/instrument?page[limit]={limit}&page[offset]={offset}"

    @classmethod
    def get_instrument_history_url(cls) -> str:
        return f"{cls.API_BASE_URL}/instrument_history"

    @classmethod
    def get_market_watch_url(cls) -> str:
        return f"{cls.API_BASE_URL}/market_watch"

    @classmethod
    def get_overview_next_data_url(cls) -> str:
        return (
            f"{cls.BASE_URL}/_next/data/{cls.NEXT_BUILD_ID}"
            f"/fr/live-market/overview.json"
        )
