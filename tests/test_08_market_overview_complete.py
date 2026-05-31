"""
Test 8: Market overview complet (live + sauvegarde JSON)
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.market_overview_scraper import MarketOverviewScraper
from src.utils.logger import get_logger, setup_logger

setup_logger()
logger = get_logger(__name__)

OUTPUT_FILE = Path(__file__).parent / "data" / "market_overview_complete.json"


def _serialize_for_json(data):
    payload = json.loads(json.dumps(data, default=str))
    if isinstance(data.get("scraped_at"), datetime):
        payload["scraped_at"] = data["scraped_at"].isoformat()
    if isinstance(data.get("date"), (date, datetime)):
        payload["date"] = data["date"].isoformat() if hasattr(data["date"], "isoformat") else str(data["date"])
    return payload


def print_section(title: str) -> None:
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)


def test_market_overview_complete():
    print("\n" + "=" * 60)
    print("TEST 8: MARKET OVERVIEW COMPLET")
    print("=" * 60)

    scraper = MarketOverviewScraper(save_to_cassandra=False)
    data = scraper.scrape_market_overview(enrich_top_movers=True)

    assert data, "Aucune donnée retournée par le scraper"

    print_section("INDICES")
    indices = data.get("indices", {})
    print(f"Nombre d'indices: {len(indices)}")
    for name, idx in indices.items():
        print(
            f"  {name:10} | valeur={idx.get('value')} | "
            f"var jour={idx.get('variation')}% | var annuelle={idx.get('annual_variation')}%"
        )

    assert "MASI" in indices, "MASI manquant"

    print_section("FUTURES MASI20")
    futures = data.get("futures", [])
    print(f"Nombre de futures: {len(futures)}")
    for future in futures:
        print(
            f"  {future.get('name')} | valeur={future.get('value')} | "
            f"variation={future.get('variation')}%"
        )

    print_section("STATS MARCHÉ")
    stats = data.get("market_stats", {})
    print(f"  Volume global : {stats.get('global_volume', 0):,.0f} MAD")
    print(f"  Capitalisation: {stats.get('market_cap', 0):,.0f} MAD")
    assert stats.get("global_volume"), "Volume global manquant"
    assert stats.get("market_cap"), "Capitalisation manquante"

    print_section("TOP 5 HAUSSES")
    gainers = data.get("top_gainers", [])
    print(f"Nombre de valeurs: {len(gainers)}")
    for idx, mover in enumerate(gainers, 1):
        print(
            f"  {idx}. {mover.get('ticker')} - {mover.get('name')} | "
            f"prix={mover.get('price')} MAD | diff={mover.get('difference')} MAD | "
            f"var={mover.get('variation')}%"
        )

    print_section("TOP 5 BAISSES")
    losers = data.get("top_losers", [])
    print(f"Nombre de valeurs: {len(losers)}")
    for idx, mover in enumerate(losers, 1):
        print(
            f"  {idx}. {mover.get('ticker')} - {mover.get('name')} | "
            f"prix={mover.get('price')} MAD | diff={mover.get('difference')} MAD | "
            f"var={mover.get('variation')}%"
        )

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        json.dump(_serialize_for_json(data), handle, indent=2, ensure_ascii=False)

    legacy_file = Path(__file__).parent / "data" / "market_overview.json"
    with open(legacy_file, "w", encoding="utf-8") as handle:
        json.dump(_serialize_for_json(data), handle, indent=2, ensure_ascii=False)

    print(f"\nResultats sauvegardes dans {OUTPUT_FILE}")
    return data


if __name__ == "__main__":
    test_market_overview_complete()
    print("\nTest market overview complet terminé avec succès.")
