# Big Data — Bourse de Casablanca Pipeline

Pipeline de données en temps réel pour la Bourse de Casablanca (BVC).
Scraping automatique, stockage Cassandra, requêtes SQL via Trino, dashboards Metabase.

---

## Architecture du pipeline

```
Site Bourse de Casablanca (casablanca-bourse.com)
        │
        ▼
[Scrapers Python] — src/scrapers/
  ├── instruments_list_scraper.py   → 1 fois/jour   → tous les instruments
  ├── instrument_details_scraper.py → toutes 15 min → ATW, BCP, MNG
  ├── historical_data_scraper.py    → 1 an initial + 1/jour → ATW, BCP, MNG
  └── market_overview_scraper.py   → toutes 2 min  → indices, stats, top movers
        │
        ▼
[Validation Pydantic] — src/storage/models.py
        │
        ▼
[Cassandra 4.1] — keyspace: bourse_data
  ├── instruments            (liste, upsert si changement)
  ├── instruments_static     (infos ISIN, secteur, …)
  ├── daily_prices           (séance du jour, 15 min)
  ├── historical_prices      (OHLC 1 an, ATW/BCP/MNG)
  ├── daily_indices          (MASI, MASI20, MASI_ESG)
  ├── market_stats           (volume global, capitalisation)
  ├── top_movers             (top 5 hausses/baisses)
  └── intraday_indices       (snapshot 2 min du MASI)
        │
        ▼
[Trino 426] — connecteur Cassandra, requêtes SQL analytiques
        │
        ▼
[Metabase v0.50.4] — Dashboards interactifs
        │
[Prefect 2.19.3] — Orchestration des flows (schedules)
```

---

## Structure du projet

```
Projet_BD/
├── src/
│   ├── scrapers/               # 4 scrapers indépendants
│   ├── parsers/                # Parsing HTML et JSON
│   ├── storage/                # Client Cassandra + modèles Pydantic
│   └── utils/                  # Config, logger, helpers
├── flows/                      # Flows Prefect (orchestration)
│   ├── instruments_flow.py     # Schedule: 18h00 Lun-Ven
│   ├── market_overview_flow.py # Schedule: toutes les 2 minutes
│   ├── details_flow.py         # Schedule: toutes les 15 minutes
│   ├── historical_flow.py      # Schedule: 19h00 Lun-Ven
│   └── deployments.py          # Enregistrement des schedules Prefect
├── tests/
│   ├── data/                   # Résultats JSON (générés par les tests)
│   ├── run_all_tests.py        # Lance tous les tests (sans Cassandra)
│   └── test_*.py               # Tests unitaires pytest
├── cassandra/
│   └── init.cql                # Schéma Cassandra (8 tables)
├── trino/catalog/
│   └── cassandra.properties    # Connecteur Trino → Cassandra
├── sql/
│   └── queries.sql             # 12 requêtes analytiques Trino
├── scripts/
│   ├── init_cassandra.py       # Initialise le schéma (1 fois)
│   ├── run_initial_load.py     # Charge 1 an d'historique (1 fois)
│   └── verify_stack.py         # Vérifie l'état de tous les services
├── docker-compose.yml          # Stack complète (Cassandra, Trino, Prefect, Metabase)
├── requirements.txt
├── .env.example                # Template de configuration
└── GUIDE_LANCEMENT.md          # Guide pas à pas
```

---

## Instruments suivis

Les détails et l'historique sont scrappés pour 3 instruments représentatifs:

| Ticker | Nom | Secteur |
|--------|-----|---------|
| ATW | Attijariwafa Bank | Banques |
| BCP | Banque Centrale Populaire | Banques |
| MNG | Managem | Mines |

Modifiable via `.env`: `TRACKED_INSTRUMENTS=ATW,BCP,MNG`

---

## Schedules des flows

| Flow | Fréquence | Données |
|------|-----------|---------|
| `instruments_flow` | 18h00 Lun-Ven | Liste complète (upsert si changement) |
| `market_overview_flow` | Toutes les 2 min | Indices + stats + top movers |
| `details_flow` | Toutes les 15 min | Prix de séance ATW, BCP, MNG |
| `historical_daily_flow` | 19h00 Lun-Ven | Dernier jour historique ATW, BCP, MNG |

---

## Prérequis

- Docker Desktop (Windows) — versions 4.0+
- Python 3.11 ou 3.12 (cassandra-driver incompatible Python 3.13)
- pip install -r requirements.txt

---

## Démarrage rapide

Voir `GUIDE_LANCEMENT.md` pour les instructions complètes pas à pas.

```bash
# 1. Copier la config
cp .env.example .env

# 2. Démarrer la stack Docker
docker-compose up -d

# 3. Tester les scrapers (sans Cassandra)
python tests/run_all_tests.py

# 4. Charger les données initiales
python scripts/run_initial_load.py

# 5. Déployer les flows Prefect
python flows/deployments.py
```

---

## Services et ports

| Service | URL | Description |
|---------|-----|-------------|
| Cassandra | localhost:9042 | Base de données NoSQL |
| Trino | http://localhost:8080 | Moteur SQL |
| Prefect | http://localhost:4200 | Orchestration (UI) |
| Metabase | http://localhost:3000 | Dashboards |
