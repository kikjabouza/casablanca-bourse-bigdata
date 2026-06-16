"""
Boucle d'exécution automatique des flows de scraping (sans Prefect worker).
Démarre automatiquement avec docker-compose et tourne en continu.

Schedules:
  - market_overview_flow  → toutes les 2 minutes (indices, stats, top movers, intraday)
  - details_flow          → toutes les 15 minutes (daily_prices + instruments_static pour 3 tickers)
"""
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flows.market_overview_flow import market_overview_flow
from flows.details_flow import details_flow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("auto_scraper")

OVERVIEW_INTERVAL_SEC = 120   # 2 minutes
DETAILS_INTERVAL_SEC  = 900   # 15 minutes


def run_overview() -> None:
    try:
        market_overview_flow()
    except Exception as exc:
        log.error(f"market_overview_flow echoue: {exc}")


def run_details() -> None:
    try:
        details_flow()
    except Exception as exc:
        log.error(f"details_flow echoue: {exc}")


def main() -> None:
    log.info("=" * 55)
    log.info("AUTO-SCRAPER BOURSE CASABLANCA — DEMARRAGE")
    log.info(f"  market_overview  : toutes les {OVERVIEW_INTERVAL_SEC // 60} min")
    log.info(f"  details (3 tickers): toutes les {DETAILS_INTERVAL_SEC // 60} min")
    log.info("=" * 55)

    last_details_ts: float = 0.0  # force exécution immédiate au démarrage

    while True:
        now = time.time()
        hhmm = datetime.now().strftime("%H:%M")

        # ── Market overview (toutes les 2 min) ───────────────────────────────
        log.info(f"[{hhmm}] >> market_overview_flow ...")
        run_overview()

        # ── Details (toutes les 15 min) ───────────────────────────────────────
        if now - last_details_ts >= DETAILS_INTERVAL_SEC:
            log.info(f"[{hhmm}] >> details_flow (ATW, BCP, MNG) ...")
            run_details()
            last_details_ts = time.time()

        elapsed = time.time() - now
        sleep_for = max(0, OVERVIEW_INTERVAL_SEC - elapsed)
        log.info(f"Prochain cycle dans {sleep_for:.0f}s ...")
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
