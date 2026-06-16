"""
Tests unitaires — Scraper détails d'un instrument.
Mode: STUB (sans Cassandra)
Usage: pytest tests/test_instrument_details.py -v
"""
import json
import os
import sys
from pathlib import Path

os.environ["CASSANDRA_STUB"] = "true"
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.utils.config import Config

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TICKER = Config().TRACKED_INSTRUMENTS[0]  # ATW par défaut
DETAILS = None


def get_details():
    global DETAILS
    if DETAILS is None:
        scraper = InstrumentDetailsScraper()
        DETAILS = scraper.scrape_instrument(TICKER)
        with open(DATA_DIR / f"{TICKER}_details.json", "w", encoding="utf-8") as f:
            json.dump(DETAILS, f, ensure_ascii=False, indent=2, default=str)
    return DETAILS


def test_details_non_vide():
    details = get_details()
    assert details, f"Aucune donnée retournée pour {TICKER}"


def test_ticker_present():
    details = get_details()
    if not details:
        pytest.skip("Données non disponibles")
    assert details.get("ticker") == TICKER


def test_prix_numerique():
    details = get_details()
    if not details:
        pytest.skip("Données non disponibles")
    price = details.get("current_price")
    if price is not None:
        assert isinstance(price, (int, float)), f"Prix invalide: {price}"
        assert price > 0, f"Prix négatif ou nul: {price}"


def test_variation_numerique():
    details = get_details()
    if not details:
        pytest.skip("Données non disponibles")
    variation = details.get("variation")
    if variation is not None:
        assert isinstance(variation, (int, float)), f"Variation invalide: {variation}"
        assert -100 <= variation <= 100, f"Variation hors plage: {variation}"


def test_champs_statiques():
    details = get_details()
    if not details:
        pytest.skip("Données non disponibles")
    # Ces champs statiques devraient être présents au moins partiellement
    has_any = any(
        details.get(k) is not None
        for k in ["isin", "sector", "currency", "nominal_value"]
    )
    assert has_any, f"Aucun champ statique trouvé pour {TICKER}"
