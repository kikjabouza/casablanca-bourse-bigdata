"""
Tests unitaires — Scraper market overview.
Mode: sans Cassandra (save_to_cassandra=False)
Usage: pytest tests/test_market_overview.py -v
"""
import json
import os
import sys
from pathlib import Path

os.environ["CASSANDRA_STUB"] = "true"
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.scrapers.market_overview_scraper import MarketOverviewScraper

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

OVERVIEW = None


def get_overview():
    global OVERVIEW
    if OVERVIEW is None:
        scraper = MarketOverviewScraper(save_to_cassandra=False)
        OVERVIEW = scraper.scrape_market_overview()
        with open(DATA_DIR / "market_overview.json", "w", encoding="utf-8") as f:
            json.dump(OVERVIEW, f, ensure_ascii=False, indent=2, default=str)
    return OVERVIEW


def test_overview_non_vide():
    overview = get_overview()
    assert overview, "Aucune donnée du market overview"


def test_indices_presents():
    overview = get_overview()
    if not overview:
        pytest.skip("Données non disponibles")
    indices = overview.get("indices", {})
    assert len(indices) > 0, "Aucun indice trouvé"
    # MASI est toujours présent
    assert "MASI" in indices, f"MASI absent. Indices trouvés: {list(indices.keys())}"


def test_valeur_masi():
    overview = get_overview()
    if not overview:
        pytest.skip("Données non disponibles")
    masi = overview.get("indices", {}).get("MASI", {})
    value = masi.get("value", 0.0)
    assert value > 0, f"Valeur MASI invalide: {value}"


def test_top_movers():
    overview = get_overview()
    if not overview:
        pytest.skip("Données non disponibles")
    gainers = overview.get("top_gainers", [])
    losers = overview.get("top_losers", [])
    # Au moins l'un des deux doit être présent
    assert len(gainers) + len(losers) > 0, "Aucun top mover trouvé"


def test_structure_top_mover():
    overview = get_overview()
    if not overview:
        pytest.skip("Données non disponibles")
    for mover in overview.get("top_gainers", [])[:3]:
        assert "ticker" in mover, f"Ticker manquant: {mover}"
        assert "variation" in mover, f"Variation manquante: {mover}"


def test_stats_marche():
    overview = get_overview()
    if not overview:
        pytest.skip("Données non disponibles")
    stats = overview.get("market_stats", {})
    # Volume ou capitalisation doit être présent
    has_stats = stats.get("global_volume", 0) > 0 or stats.get("market_cap", 0) > 0
    if not has_stats:
        pytest.skip("Stats de marché non disponibles (API peut être indisponible)")
