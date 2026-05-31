# src/utils/config.py
import os
from typing import Dict

import requests
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration centralisée pour tous les scrapers"""

    BASE_URL = os.getenv("BOURSE_BASE_URL", "https://www.casablanca-bourse.com")
    OVERVIEW_URL = f"{BASE_URL}/fr/live-market/overview"
    INSTRUMENT_BASE_URL = f"{BASE_URL}/fr/live-market/instruments"
    API_BASE_URL = f"{BASE_URL}/api/proxy/fr/api/bourse_data"
    NEXT_BUILD_ID = os.getenv("NEXT_BUILD_ID", "k6VYoXBS432b__PEHJ2s2")

    HEADERS: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    API_HEADERS: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/vnd.api+json",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Referer": BASE_URL,
    }

    CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
    CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
    CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "bourse_data")
    CASSANDRA_STUB = os.getenv("CASSANDRA_STUB", "false").lower() == "true"

    TRINO_HOST = os.getenv("TRINO_HOST", "localhost")
    TRINO_PORT = int(os.getenv("TRINO_PORT", "8080"))
    TRINO_CATALOG = os.getenv("TRINO_CATALOG", "cassandra")
    TRINO_SCHEMA = os.getenv("TRINO_SCHEMA", "bourse_data")
    TRINO_USER = os.getenv("TRINO_USER", "reporting")

    PREFECT_API_URL = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")
    METABASE_URL = os.getenv("METABASE_URL", "http://localhost:3000")

    ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "2.0"))

    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.5"))
    BULK_REQUEST_DELAY = float(os.getenv("BULK_REQUEST_DELAY", "1.0"))

    DEFAULT_LIMIT = 250
    MAX_OFFSET = 5000
    DEFAULT_START_DATE = "2010-01-01"

    INDEX_TAXONOMY_IDS = {
        "MASI20": 512343,
        "MASI": 512335,
        "MASI ESG": 512320,
    }

    @classmethod
    def get_session(cls) -> requests.Session:
        """Retourne une session HTTP réutilisable avec les headers par défaut."""
        session = requests.Session()
        session.headers.update(cls.HEADERS)
        return session

    @classmethod
    def get_instrument_api_url(cls, instrument_id: int) -> str:
        return f"{cls.API_BASE_URL}/instrument_history"

    @classmethod
    def get_market_watch_url(cls) -> str:
        return f"{cls.API_BASE_URL}/market_watch"

    @classmethod
    def get_overview_next_data_url(cls) -> str:
        return f"{cls.BASE_URL}/_next/data/{cls.NEXT_BUILD_ID}/fr/live-market/overview.json"
