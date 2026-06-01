#!/usr/bin/env python3
"""
GUIDE RAPIDE - Comment utiliser le projet après les modifications

Exécutez ce script pour comprendre les changements et comment tester
"""

import sys
from pathlib import Path

def print_section(title, emoji="📋"):
    print(f"\n{emoji} {title}")
    print("=" * 70)

def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " GUIDE RAPIDE - MODIFICATIONS DU PROJET ".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Section 1: Résumé des modifications
    print_section("1️⃣ RÉSUMÉ DES MODIFICATIONS", "📝")
    print("""
    ✅ SUPPRIMÉS:
       • src/scrapers/masi_realtime_scraper.py (redondance avec market_overview)
       • 6 fichiers de tests obsolètes (test_01, test_03, test_05, test_06, etc.)
       
    ✅ CRÉÉS/MODIFIÉS:
       • tests/test_all_scrapers.py (test global)
       • src/main.py (refactorisé pour scraping complet)
       • src/storage/cassandra_client.py (mode test intégré)
       • cassandra/data/ (dossier pour résultats scraping)
       • MODIFICATIONS.md (documentation complète)
       • TEST_GUIDE.py (guide de test interactif)
       
    ✅ TESTS CONSERVÉS:
       • test_03_instruments_list_v2.py
       • test_04_instrument_details.py
       • test_02_historical_data.py
       • test_08_market_overview_complete.py
    """)
    
    # Section 2: Comment scraper les données
    print_section("2️⃣ COMMENT SCRAPER LES DONNÉES", "🚀")
    print("""
    OPTION 1 - Module Python (recommandé):
    ────────────────────────────────────────
    python -m src.main              # Scraping COMPLET
    python -m src.main --daily      # Mise à jour quotidienne
    python -m src.main --overview   # Market overview seulement
    
    
    OPTION 2 - Script:
    ──────────────────
    python scripts/scrape.py              # Scraping COMPLET
    python scripts/scrape.py --daily      # Mise à jour quotidienne
    python scripts/scrape.py --overview   # Market overview seulement
    
    
    IMPORTANT - Points clés:
    ─────────────────────────
    • Scrape TOUTES les données (pas de limites)
    • Sans orchestration Prefect (à ajouter plus tard)
    • Résultats stockés en JSON dans cassandra/data/
    • Prêt pour insertion dans Cassandra
    """)
    
    # Section 3: Tests unitaires
    print_section("3️⃣ TESTS UNITAIRES (SANS CASSANDRA)", "🧪")
    print("""
    Les tests fonctionnent INDÉPENDAMMENT de Cassandra:
    
    Exécuter les tests individuels:
    ───────────────────────────────
    python -m pytest tests/test_03_instruments_list_v2.py -v
    python -m pytest tests/test_04_instrument_details.py -v
    python -m pytest tests/test_02_historical_data.py -v
    python -m pytest tests/test_08_market_overview_complete.py -v
    
    
    Exécuter TOUS les tests à la fois:
    ──────────────────────────────────
    python tests/test_all_scrapers.py
    
    Résultats sauvegardés dans:
    → tests/data/all_tests_results.json
    
    
    Mode test automatique:
    ──────────────────────
    Les tests utilisent CassandraClient(test_mode=True)
    → Données en JSON uniquement
    → Pas de connexion Cassandra requise
    → Parfait pour développement/debug
    """)
    
    # Section 4: Données générées
    print_section("4️⃣ OÙ SONT LES DONNÉES?", "📊")
    print("""
    RÉSULTATS DE TEST:
    tests/data/
      ├── all_instruments.json           # Liste instruments
      ├── MNG_details.json               # Détails exemple
      ├── MNG_historical.json            # Historique exemple
      ├── market_overview_complete.json  # Vue d'ensemble
      └── all_tests_results.json         # Résumé tests
    
    
    RÉSULTATS SCRAPING:
    cassandra/data/
      ├── instruments_static/            # Détails instruments
      ├── instruments_prices/            # Données historiques
      └── market_overview/               # Indices + stats + movers
    
    
    LOGS:
    logs/
      └── [fichiers de log du scraping]
    """)
    
    # Section 5: Modes Cassandra
    print_section("5️⃣ MODES CASSANDRA", "🗄️")
    print("""
    Mode TEST (pour développement):
    ───────────────────────────────
    cassandra = CassandraClient(test_mode=True)
    ✓ Pas de connexion Cassandra
    ✓ Données en fichiers JSON
    ✓ Parfait pour tests et debug
    
    Utilisé par: tests/test_*.py
    
    
    Mode PRODUCTION (avec Cassandra réelle):
    ───────────────────────────────────────
    cassandra = CassandraClient(test_mode=False)
    ✓ Tente connexion Cassandra
    ✓ Données dans base de données
    ✓ Prêt pour Metabase/Trino
    
    Utilisé par: src/main.py
    """)
    
    # Section 6: Vérifier la stack
    print_section("6️⃣ VÉRIFIER LA STACK (CASSANDRA/TRINO/METABASE)", "✔️")
    print("""
    Vérifier que tous les services sont accessibles:
    ─────────────────────────────────────────────────
    python scripts/verify_stack.py
    
    Vérifie:
    • Cassandra (localhost:9042)
    • Trino (localhost:8080)
    • Metabase (localhost:3000)
    """)
    
    # Section 7: Workflow complet
    print_section("7️⃣ WORKFLOW COMPLET", "🔄")
    print("""
    1. Scraper les données:
       python -m src.main
       → Génère fichiers JSON dans cassandra/data/
    
    2. Valider avec tests:
       python tests/test_all_scrapers.py
       → Vérifie intégrité des scrapers
    
    3. Vérifier Cassandra:
       python scripts/verify_stack.py
       → Vérifie connexion et services
    
    4. Insérer dans Cassandra:
       (Via cassandra_client.py dans production)
       → Mode production de CassandraClient
    
    5. Requêtes Trino/Metabase:
       (Via sql/queries.sql)
       → Dashboards prêts pour analyse
    
    6. Orchestration Prefect (à venir):
       (Via flows/ - à ajouter)
       → Mises à jour automatiques
    """)
    
    # Section 8: Ressources
    print_section("8️⃣ RESSOURCES", "📚")
    print("""
    Documentation:
    ──────────────
    • MODIFICATIONS.md      - Documentation complète des changements
    • src/main.py          - Code principal avec docstrings
    • cassandra/data/README.md - Guide stockage
    
    
    Fichiers clés:
    ──────────────
    • src/main.py          - Orchestrateur de scraping
    • src/scrapers/        - Tous les scrapers
    • tests/test_all_scrapers.py - Tests globaux
    • scripts/             - Scripts utilitaires
    
    
    Configuration:
    ───────────────
    • .env                 - Variables d'environnement
    • src/utils/config.py  - Configuration applicative
    • cassandra/init.cql   - Schéma Cassandra
    """)
    
    # Section 9: Commandes rapides
    print_section("9️⃣ COMMANDES RAPIDES", "⚡")
    print("""
    # Scraping complet
    python -m src.main
    
    # Tous les tests
    python tests/test_all_scrapers.py
    
    # Vérifier services
    python scripts/verify_stack.py
    
    # Un seul test
    python -m pytest tests/test_04_instrument_details.py -v
    
    # Voir les résultats
    cat tests/data/all_tests_results.json
    cat cassandra/data/README.md
    
    # Mode interactif
    python TEST_GUIDE.py
    """)
    
    # Section 10: Support
    print_section("🔟 QUESTIONS?", "❓")
    print("""
    Voir MODIFICATIONS.md pour la documentation complète.
    
    Points clés à retenir:
    ──────────────────────
    1. Tests = indépendants de Cassandra (mode JSON)
    2. Scraping = complet, sans limites, sans Prefect
    3. Données = JSON dans cassandra/data/ avant insertion
    4. Cassandra = mode production (test_mode=False)
    5. Documentation = MODIFICATIONS.md
    
    
    Prochaines étapes (à faire par vous):
    ─────────────────────────────────────
    1. Tester le scraping: python -m src.main
    2. Vérifier les résultats: cat cassandra/data/README.md
    3. Lancer les tests: python tests/test_all_scrapers.py
    4. Configurer Cassandra pour production
    5. Intégrer Prefect pour orchestration
    6. Préparer Metabase dashboards
    """)
    
    print("\n" + "=" * 70)
    print("✅ MODIFICATIONS TERMINÉES - PRÊT POUR UTILISATION".center(70))
    print("=" * 70 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
