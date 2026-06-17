"""
Script de déploiement des flows Prefect avec leurs schedules.

Usage (après démarrage du serveur Prefect):
    python flows/deployments.py

Schedules configurés:
  - instruments-daily     : Lun-Ven 18h00 (liste complète, upsert si changement)
  - market-overview-2min  : toutes les 2 minutes (indices, stats, top movers)
  - details-15min         : toutes les 15 minutes (10 instruments: ATW,BCP,IAM,MNG,ADH,CIH,ALM,DHO,HPS,ATH)
  - historical-daily      : Lun-Ven 19h00 (ajout du dernier jour historique pour les 10 instruments)
"""
import os
import sys
from datetime import timedelta
from pathlib import Path

# Ajouter la racine du projet au path Python
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("PREFECT_API_URL", "http://localhost:4200/api")

from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule, IntervalSchedule

from flows.instruments_flow import instruments_flow
from flows.market_overview_flow import market_overview_flow
from flows.details_flow import details_flow
from flows.historical_flow import historical_daily_flow


def deploy_all() -> None:
    print("=" * 60)
    print("DEPLOIEMENT DES FLOWS PREFECT")
    print("Serveur Prefect: http://localhost:4200")
    print("=" * 60)

    # 1. Liste instruments — 1 fois/jour Lun-Ven 18h00
    dep_instruments = Deployment.build_from_flow(
        flow=instruments_flow,
        name="instruments-daily",
        description="Scrape tous les instruments, insert uniquement si changements",
        schedule=CronSchedule(cron="0 18 * * 1-5", timezone="Africa/Casablanca"),
        tags=["bourse", "instruments", "daily"],
    )

    # 2. Market overview — toutes les 2 minutes
    dep_market = Deployment.build_from_flow(
        flow=market_overview_flow,
        name="market-overview-2min",
        description="Mise à jour indices + stats + top movers toutes les 2 minutes",
        schedule=IntervalSchedule(interval=timedelta(minutes=2)),
        tags=["bourse", "market", "intraday"],
    )

    # 3. Détails 10 instruments — toutes les 15 minutes
    dep_details = Deployment.build_from_flow(
        flow=details_flow,
        name="details-15min",
        description="Détails de séance pour les 10 instruments suivis (TRACKED_INSTRUMENTS) toutes les 15 minutes",
        schedule=IntervalSchedule(interval=timedelta(minutes=15)),
        tags=["bourse", "details", "intraday"],
    )

    # 4. Historique quotidien — Lun-Ven 19h00
    dep_historical = Deployment.build_from_flow(
        flow=historical_daily_flow,
        name="historical-daily",
        description="Ajout du dernier jour historique pour les 10 instruments suivis",
        schedule=CronSchedule(cron="0 19 * * 1-5", timezone="Africa/Casablanca"),
        tags=["bourse", "historical", "daily"],
    )

    print("\nDeploiement en cours...")
    dep_instruments.apply()
    print("  [OK] instruments-daily           (Lun-Ven 18:00)")
    dep_market.apply()
    print("  [OK] market-overview-2min        (toutes les 2 min)")
    dep_details.apply()
    print("  [OK] details-15min               (toutes les 15 min)")
    dep_historical.apply()
    print("  [OK] historical-daily            (Lun-Ven 19:00)")

    print("\nTous les flows sont deployes!")
    print("Interface Prefect: http://localhost:4200")
    print("\nPour lancer un flow manuellement:")
    print("  prefect deployment run instruments-daily/instruments-daily")
    print("  prefect deployment run market-overview-flow/market-overview-2min")
    print("  prefect deployment run details-flow/details-15min")
    print("  prefect deployment run historical-daily-flow/historical-daily")


if __name__ == "__main__":
    deploy_all()
