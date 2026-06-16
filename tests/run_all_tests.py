"""
Tests complets des scrapers — INDEPENDANTS de Cassandra et Prefect.
Les résultats sont sauvegardés en JSON dans tests/data/.

Usage:
    python tests/run_all_tests.py        # Tous les tests
    python tests/run_all_tests.py --list # Test liste instruments uniquement
    python tests/run_all_tests.py --overview  # Test market overview uniquement
"""
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Racine du projet
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Mode stub: aucune connexion Cassandra
os.environ["CASSANDRA_STUB"] = "true"

from src.scrapers.historical_data_scraper import HistoricalDataScraper
from src.scrapers.instrument_details_scraper import InstrumentDetailsScraper
from src.scrapers.instruments_list_scraper import InstrumentsListScraper
from src.scrapers.market_overview_scraper import MarketOverviewScraper
from src.utils.config import Config
from src.utils.logger import setup_logger

setup_logger()

DATA_DIR = ROOT / "tests" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ─── Utilitaire ──────────────────────────────────────────────────────────────

def _save(data, filename: str) -> Path:
    """Sauvegarde data en JSON dans tests/data/."""
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return path


def _header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# ─── Tests individuels ────────────────────────────────────────────────────────

def test_instruments_list() -> dict:
    _header("TEST 1 — Liste complète des instruments")
    scraper = InstrumentsListScraper()
    instruments = scraper.scrape_instruments_list()

    path = _save(instruments, "all_instruments.json")
    result = {
        "test": "instruments_list",
        "timestamp": datetime.now().isoformat(),
        "count": len(instruments),
        "sample": instruments[:5],
        "status": "OK" if instruments else "FAILED",
    }
    _save(result, "result_instruments_list.json")

    print(f"  -> {len(instruments)} instruments trouves")
    if instruments:
        print(f"  -> Exemple: {instruments[0]}")
    print(f"  -> Fichier: {path}")
    print(f"  -> Status: {result['status']}")
    return result


def test_instrument_details() -> dict:
    config = Config()
    ticker = config.TRACKED_INSTRUMENTS[0]
    _header(f"TEST 2 — Détails de l'instrument: {ticker}")

    scraper = InstrumentDetailsScraper()
    details = scraper.scrape_instrument(ticker)

    path = _save(details, f"{ticker}_details.json")
    result = {
        "test": "instrument_details",
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "fields_count": len(details),
        "data": details,
        "status": "OK" if details else "FAILED",
    }
    _save(result, f"result_{ticker}_details.json")

    print(f"  -> {len(details)} champs extraits")
    for key in ["current_price", "variation", "sector", "isin", "volume"]:
        print(f"  -> {key}: {details.get(key)}")
    print(f"  -> Fichier: {path}")
    print(f"  -> Status: {result['status']}")
    return result


def test_historical_data() -> dict:
    config = Config()
    ticker = config.TRACKED_INSTRUMENTS[0]
    start_date = (date.today() - timedelta(days=30)).isoformat()
    _header(f"TEST 3 — Historique {ticker} (30 derniers jours)")

    scraper = HistoricalDataScraper()
    records = scraper.scrape_historical_data(ticker, start_date=start_date)

    path = _save(records, f"{ticker}_historical_30d.json")
    result = {
        "test": "historical_data",
        "ticker": ticker,
        "start_date": start_date,
        "timestamp": datetime.now().isoformat(),
        "records_count": len(records),
        "sample": records[:3] if records else [],
        "status": "OK" if records else "FAILED",
    }
    _save(result, f"result_{ticker}_historical.json")

    print(f"  -> {len(records)} enregistrements historiques")
    if records:
        first, last = records[0], records[-1]
        print(f"  -> Premier: {first.get('date')} | close={first.get('close_price')}")
        print(f"  -> Dernier: {last.get('date')} | close={last.get('close_price')}")
    print(f"  -> Fichier: {path}")
    print(f"  -> Status: {result['status']}")
    return result


def test_market_overview() -> dict:
    _header("TEST 4 — Market Overview (indices, stats, top movers)")

    scraper = MarketOverviewScraper(save_to_cassandra=False)
    overview = scraper.scrape_market_overview()

    path = _save(overview, "market_overview.json")
    result = {
        "test": "market_overview",
        "timestamp": datetime.now().isoformat(),
        "indices": list(overview.get("indices", {}).keys()),
        "top_gainers_count": len(overview.get("top_gainers", [])),
        "top_losers_count": len(overview.get("top_losers", [])),
        "data": overview,
        "status": "OK" if overview else "FAILED",
    }
    _save(result, "result_market_overview.json")

    print(f"  -> Indices: {result['indices']}")
    for idx, data in overview.get("indices", {}).items():
        print(f"     {idx}: {data.get('value')} ({data.get('variation'):+.2f}%)")
    print(f"  -> Top gainers: {result['top_gainers_count']}, Top losers: {result['top_losers_count']}")
    print(f"  -> Stats: {overview.get('market_stats')}")
    print(f"  -> Fichier: {path}")
    print(f"  -> Status: {result['status']}")
    return result


# ─── Exécution principale ─────────────────────────────────────────────────────

def main() -> int:
    print("\n" + "=" * 60)
    print("  TESTS SCRAPERS — Bourse de Casablanca")
    print("  Mode: STUB (sans Cassandra, sans Prefect)")
    print(f"  Resultats: {DATA_DIR}")
    print("=" * 60)

    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    test_funcs = {
        "--list": [test_instruments_list],
        "--details": [test_instrument_details],
        "--historical": [test_historical_data],
        "--overview": [test_market_overview],
    }
    funcs = test_funcs.get(arg, [
        test_instruments_list,
        test_instrument_details,
        test_historical_data,
        test_market_overview,
    ])

    all_results = {"run_at": datetime.now().isoformat(), "tests": {}}
    for func in funcs:
        try:
            res = func()
            all_results["tests"][res["test"]] = res
        except Exception as exc:
            name = func.__name__.replace("test_", "")
            print(f"  ERREUR: {exc}")
            all_results["tests"][name] = {"status": "ERROR", "error": str(exc)}

    all_ok = all(t.get("status") == "OK" for t in all_results["tests"].values())
    all_results["overall_status"] = "ALL_PASSED" if all_ok else "SOME_FAILED"
    _save(all_results, "all_tests_results.json")

    print(f"\n{'=' * 60}")
    print(f"  RESULTAT GLOBAL: {all_results['overall_status']}")
    print(f"  Rapport: {DATA_DIR / 'all_tests_results.json'}")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
