# flows/intraday_monitoring_flow.py
from datetime import datetime, time as dt_time
from typing import Dict, List

from prefect import flow, get_run_logger, task

from src.scrapers.masi_realtime_scraper import MASIRealtimeScraper
from src.storage.cassandra_client import CassandraClient
from src.utils.logger import setup_logger

MARKET_OPEN = dt_time(9, 30)
MARKET_CLOSE = dt_time(16, 0)
ANOMALY_THRESHOLD = 2.0


@task(name="scrape-intraday-indices", retries=2, retry_delay_seconds=10, log_prints=True)
def scrape_intraday_indices() -> Dict[str, dict]:
    scraper = MASIRealtimeScraper()
    return scraper.scrape_all_indices()


@task(name="detect-anomalies", log_prints=True)
def detect_anomalies(points: Dict[str, dict]) -> List[dict]:
    alerts = []
    scraper = MASIRealtimeScraper()

    for index_name, point in points.items():
        previous = scraper.get_latest_value(index_name)
        current = point.get("value")
        if previous and current:
            variation = abs((current - previous) / previous * 100)
            if variation >= ANOMALY_THRESHOLD:
                alerts.append(
                    {
                        "index_name": index_name,
                        "previous": previous,
                        "current": current,
                        "variation_pct": round(variation, 2),
                        "timestamp": point.get("timestamp"),
                    }
                )
    return alerts


@flow(name="intraday-monitoring-flow", description="Monitoring intraday des indices MASI")
def intraday_monitoring_flow(force: bool = False):
    setup_logger()
    logger = get_run_logger()
    now = datetime.now()

    if not force and not (MARKET_OPEN <= now.time() <= MARKET_CLOSE):
        logger.info("Hors horaires de marché, monitoring ignoré")
        return

    CassandraClient()
    points = scrape_intraday_indices()
    alerts = detect_anomalies(points)

    logger.info(f"{len(points)} indices scrapés, {len(alerts)} alertes")
    for alert in alerts:
        logger.warning(
            f"Variation anormale {alert['index_name']}: "
            f"{alert['previous']} -> {alert['current']} ({alert['variation_pct']}%)"
        )


if __name__ == "__main__":
    intraday_monitoring_flow(force=True)
