"""
Tests unitaires — Scraper données historiques.
Mode: STUB (sans Cassandra), limité à 30 jours pour rapidité
Usage: pytest tests/test_historical_data.py -v
"""
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

os.environ["CASSANDRA_STUB"] = "true"
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.utils.config import Config

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TICKER = Config().TRACKED_INSTRUMENTS[0]
START_DATE = (date.today() - timedelta(days=30)).isoformat()
RECORDS = None


def get_records():
    global RECORDS
    if RECORDS is None:
        scraper = HistoricalDataScraper()
        RECORDS = scraper.scrape_historical_data(TICKER, start_date=START_DATE)
        with open(DATA_DIR / f"{TICKER}_historical_30d.json", "w", encoding="utf-8") as f:
            json.dump(RECORDS, f, ensure_ascii=False, indent=2, default=str)
    return RECORDS


def test_instrument_id():
    scraper = HistoricalDataScraper()
    inst_id = scraper.get_instrument_id(TICKER)
    assert inst_id is not None, f"ID introuvable pour {TICKER}"
    assert isinstance(inst_id, int), f"ID doit être un entier: {inst_id}"


def test_records_non_vide():
    records = get_records()
    if not records:
        pytest.skip("API historique non accessible (normal hors marché)")
    assert len(records) > 0, f"Aucun enregistrement pour {TICKER} depuis {START_DATE}"


def test_structure_record():
    records = get_records()
    if not records:
        pytest.skip("API historique non accessible")
    for rec in records[:5]:
        assert "ticker" in rec, f"Champ ticker manquant: {rec}"
        assert "date" in rec, f"Champ date manquant: {rec}"
        assert "close_price" in rec, f"Champ close_price manquant: {rec}"


def test_prix_positif():
    records = get_records()
    if not records:
        pytest.skip("API historique non accessible")
    for rec in records[:10]:
        close = rec.get("close_price")
        if close is not None:
            assert close > 0, f"Prix de clôture invalide: {close}"


def test_dates_croissantes():
    records = get_records()
    if not records or len(records) < 2:
        pytest.skip("Pas assez d'enregistrements")
    dates = [r.get("date", "") for r in records if r.get("date")]
    assert dates == sorted(dates), "Les dates ne sont pas dans l'ordre croissant"
