"""
Point d'entrée Prefect pour le scraper-worker.
Utilise prefect.serve() qui :
  1. Enregistre les deployments sur le serveur Prefect (visible dans l'UI)
  2. Exécute les flows selon le schedule défini
  3. Rapporte chaque run (statut, durée, erreurs) dans l'UI http://localhost:4200

Ce script remplace à la fois le Prefect worker ET l'enregistrement des deployments.
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prefect import serve

from flows.market_overview_flow import market_overview_flow
from flows.details_flow import details_flow


def main() -> None:
    print("=" * 60)
    print("PREFECT SERVE — BOURSE CASABLANCA")
    print("UI : http://localhost:4200")
    print("=" * 60)

    # Deployment 1 : market overview toutes les 2 minutes
    market_deployment = market_overview_flow.to_deployment(
        name="market-overview-2min",
        description="Indices (MASI/MASI20), stats globales, top movers, snapshot intraday",
        interval=timedelta(minutes=2),
        tags=["bourse", "market", "intraday"],
    )

    # Deployment 2 : détails des 3 instruments toutes les 15 minutes
    details_deployment = details_flow.to_deployment(
        name="details-15min",
        description="Cours de séance + infos statiques pour ATW, BCP, MNG",
        interval=timedelta(minutes=15),
        tags=["bourse", "details", "intraday"],
    )

    print("Deployments enregistrés :")
    print("  → market-overview-2min  : toutes les 2 minutes")
    print("  → details-15min         : toutes les 15 minutes")
    print("\nVisualiser les runs : http://localhost:4200/deployments")
    print("(Ctrl+C pour arrêter)\n")

    # serve() bloque et exécute les flows selon leur schedule
    serve(market_deployment, details_deployment)


if __name__ == "__main__":
    main()
