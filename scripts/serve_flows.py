"""
Point d'entrée Prefect pour le scraper-worker.
Utilise prefect.serve() qui :
  1. Enregistre les deployments sur le serveur Prefect (visible dans l'UI)
  2. Exécute les flows selon le schedule défini
  3. Rapporte chaque run (statut, durée, erreurs) dans l'UI http://localhost:4200

Flows actifs :
  - market-overview-2min  : toutes les 2 minutes (indices, stats, top movers)
  - details-15min         : toutes les 15 minutes (10 instruments)
  - instruments-daily     : Lun-Ven 18h00 — mise à jour catalogue instruments
  - historical-daily      : Lun-Ven 19h00 — ajout du dernier jour OHLC
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prefect import serve

from flows.market_overview_flow import market_overview_flow
from flows.details_flow import details_flow
from flows.instruments_flow import instruments_flow
from flows.historical_flow import historical_daily_flow


def main() -> None:
    print("=" * 60)
    print("PREFECT SERVE — BOURSE CASABLANCA")
    print("UI : http://localhost:4200")
    print("=" * 60)

    # Deployment 1 : market overview toutes les 2 minutes
    market_deployment = market_overview_flow.to_deployment(
        name="market-overview-2min",
        description="Indices (MASI/MASI20/MASI_ESG), stats globales, top movers, snapshot intraday",
        interval=timedelta(minutes=2),
        tags=["bourse", "market", "intraday"],
    )

    # Deployment 2 : détails des 10 instruments toutes les 15 minutes
    details_deployment = details_flow.to_deployment(
        name="details-15min",
        description="Cours de séance + infos statiques pour les 10 instruments suivis (TRACKED_INSTRUMENTS)",
        interval=timedelta(minutes=15),
        tags=["bourse", "details", "intraday"],
    )

    # Deployment 3 : liste des instruments 1 fois/jour Lun-Ven 18h00 Casablanca (= 17h00 UTC)
    # Maroc = UTC+1 permanent (pas de changement d'heure depuis 2018)
    instruments_deployment = instruments_flow.to_deployment(
        name="instruments-daily",
        description="Mise à jour quotidienne du catalogue complet des instruments (upsert si changement)",
        cron="0 17 * * 1-5",
        tags=["bourse", "instruments", "daily"],
    )

    # Deployment 4 : historique OHLC 1 fois/jour Lun-Ven 19h00 Casablanca (= 18h00 UTC)
    historical_deployment = historical_daily_flow.to_deployment(
        name="historical-daily",
        description="Ajout du dernier jour OHLC pour les 10 instruments suivis (après clôture 19h00)",
        cron="0 18 * * 1-5",
        tags=["bourse", "historical", "daily"],
    )

    print("Deployments enregistrés :")
    print("  → market-overview-2min  : toutes les 2 minutes")
    print("  → details-15min         : toutes les 15 minutes (10 instruments)")
    print("  → instruments-daily     : Lun-Ven 18h00 (Casablanca)")
    print("  → historical-daily      : Lun-Ven 19h00 (Casablanca)")
    print("\nVisualiser les runs : http://localhost:4200/deployments")
    print("(Ctrl+C pour arrêter)\n")

    # serve() bloque et exécute les 4 flows selon leurs schedules
    serve(market_deployment, details_deployment, instruments_deployment, historical_deployment)


if __name__ == "__main__":
    main()
