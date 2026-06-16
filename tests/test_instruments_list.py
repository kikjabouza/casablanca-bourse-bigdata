"""
Tests unitaires — Scraper liste des instruments.
Mode: STUB (sans Cassandra)
Usage: pytest tests/test_instruments_list.py -v
"""
import json
import os
import sys
from pathlib import Path

# Mode stub obligatoire
os.environ["CASSANDRA_STUB"] = "true"
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.scrapers.instruments_list_scraper import InstrumentsListScraper

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

INSTRUMENTS = None  # cache entre tests


def get_instruments():
    global INSTRUMENTS
    if INSTRUMENTS is None:
        scraper = InstrumentsListScraper()
        INSTRUMENTS = scraper.scrape_instruments_list()
        with open(DATA_DIR / "all_instruments.json", "w", encoding="utf-8") as f:
            json.dump(INSTRUMENTS, f, ensure_ascii=False, indent=2)
    return INSTRUMENTS


def test_liste_non_vide():
    instruments = get_instruments()
    assert len(instruments) > 0, "La liste d'instruments ne doit pas être vide"


def test_structure_instrument():
    instruments = get_instruments()
    assert len(instruments) > 0
    for inst in instruments[:10]:
        assert "ticker" in inst, f"Champ 'ticker' manquant: {inst}"
        assert "name" in inst, f"Champ 'name' manquant: {inst}"
        assert "url" in inst, f"Champ 'url' manquant: {inst}"


def test_ticker_valide():
    instruments = get_instruments()
    for inst in instruments[:20]:
        ticker = inst.get("ticker", "")
        assert len(ticker) >= 2, f"Ticker trop court: '{ticker}'"
        assert ticker.isalnum() or "-" in ticker, f"Ticker invalide: '{ticker}'"


def test_ticker_unique():
    instruments = get_instruments()
    tickers = [i["ticker"] for i in instruments]
    assert len(tickers) == len(set(tickers)), "Des tickers en double détectés"


def test_url_format():
    instruments = get_instruments()
    for inst in instruments[:20]:
        url = inst.get("url", "")
        assert url, f"URL vide pour {inst.get('ticker')}"
