# PROJECT STATUS — Bourse de Casablanca Big Data

Dernière mise à jour : 31 mai 2026

## Structure du projet

```
casablanca-bourse-bigdata/
├── docker-compose.yml          # Stack Docker (Cassandra, Prefect, Trino, Metabase)
├── requirements.txt            # Dépendances Python
├── PROJECT_STATUS.md           # Ce fichier
├── flows/                      # Orchestration Prefect
│   ├── base_flow.py            # Classe de base (retries, logging)
│   ├── initial_load_flow.py    # Chargement initial unique
│   ├── daily_update_flow.py    # Mise à jour quotidienne 17h
│   ├── intraday_monitoring_flow.py  # Monitoring MASI toutes les 2 min
│   └── deployment.yaml         # Configuration des déploiements Prefect
├── src/
│   ├── main.py                 # Orchestrateur CLI (initial / daily)
│   ├── scrapers/               # Scrapers métier
│   │   ├── base_scraper.py
│   │   ├── instruments_list_scraper.py
│   │   ├── instrument_details_scraper.py
│   │   ├── historical_data_scraper.py
│   │   ├── market_overview_scraper.py
│   │   └── masi_realtime_scraper.py
│   ├── parsers/                # Parseurs HTML / JSON
│   │   ├── html_parser.py
│   │   └── json_parser.py
│   ├── storage/                # Persistance Cassandra
│   │   ├── cassandra_client.py
│   │   ├── models.py
│   │   └── data_validator.py
│   └── utils/                  # Config, logs, helpers
│       ├── config.py
│       ├── logger.py
│       └── helpers.py
└── tests/                      # Tests unitaires et scripts de validation
    ├── test_01 … test_08
    ├── run_all_tests.py
    ├── view_all_results.py
    └── data/                   # JSON générés par les tests
```

| Dossier | Rôle |
|---------|------|
| `src/scrapers/` | Collecte des données depuis le site/API Bourse de Casablanca |
| `src/parsers/` | Extraction structurée depuis HTML et JSON API |
| `src/storage/` | Modèles Pydantic, validation et client Cassandra |
| `flows/` | Pipelines Prefect planifiés |
| `tests/` | Validation des scrapers et sauvegarde JSON de contrôle |

---

## Schéma Cassandra

**Keyspace** : `bourse_data` (SimpleStrategy, RF=1)

### `instruments_static`
| Colonne | Type | Description |
|---------|------|-------------|
| `ticker` | text PK | Symbole boursier |
| `isin`, `sector`, `listing_date`, `shares_count`, `nominal_value`, `trading_cycle`, `currency` | divers | Métadonnées statiques |
| `updated_at` | timestamp | Horodatage de mise à jour |

### `daily_prices`
| Colonne | Type | Description |
|---------|------|-------------|
| PK | `(ticker, date)` | Cours de séance quotidiens |
| `open/high/low/close_price`, `volume`, `quantity`, `trades_count`, `market_cap`, `variation`, `var_ytd` | decimal/int | Données OHLCV |
| `scraped_at` | timestamp | Horodatage scraping |

### `historical_prices`
| Colonne | Type | Description |
|---------|------|-------------|
| PK | `(ticker, date)` | Historique long terme |
| `adjusted_close` | decimal | Cours ajusté (splits/ratios) |

### `daily_indices`
| Colonne | Type | Description |
|---------|------|-------------|
| PK | `(index_name, date)` | MASI, MASI20, MASI_ESG |
| `value`, `variation`, `annual_variation` | decimal | Valeur et variations |

### `market_stats`
| Colonne | Type | Description |
|---------|------|-------------|
| PK | `date` | Stats globales journalières |
| `global_volume`, `market_cap` | decimal | Volume et capitalisation |

### `top_movers`
| Colonne | Type | Description |
|---------|------|-------------|
| PK | `(date, direction, rank)` | Top 5 hausses/baisses |
| `ticker`, `company_name`, `price`, `variation` | divers | Détail du mouvement |

### `intraday_indices`
| Colonne | Type | Description |
|---------|------|-------------|
| PK | `(index_name, date, timestamp)` | Points MASI intraday |
| `value`, `scraped_at` | decimal/timestamp | Valeur et collecte |

---

## Données scrapées

| Scraper | Données extraites | Fréquence | Source | Table Cassandra |
|---------|-------------------|-----------|--------|-----------------|
| `instruments_list_scraper` | Liste tickers + IDs | Initial + daily | HTML / Next.js | — |
| `instrument_details_scraper` | ISIN, secteur, séance | Daily | HTML | `instruments_static`, `daily_prices` |
| `historical_data_scraper` | OHLCV historique | Initial + daily | API JSON | `historical_prices` |
| `market_overview_scraper` | Indices, stats, top movers, futures | Daily | HTML + Next.js + API | `daily_indices`, `market_stats`, `top_movers` |
| `masi_realtime_scraper` | MASI / MASI20 / MASI_ESG live | Toutes les 2 min | API JSON | `intraday_indices` |

---

## Workflow d'exécution

### Étape 1 — Chargement initial
1. Scraper la liste des instruments
2. Pour chaque instrument : détails statiques + historique complet
3. Scraper le market overview complet
4. Persister dans Cassandra

### Étape 2 — Mise à jour quotidienne (17h00)
1. Mettre à jour les données de séance de tous les instruments
2. Ajouter la journée courante à l'historique
3. Mettre à jour indices, stats marché et top movers

### Étape 3 — Monitoring intraday
1. Scraper MASI / MASI20 / MASI_ESG toutes les 2 minutes (9h30–16h00)
2. Détecter les variations anormales (> 2 %)
3. Sauvegarder les points dans `intraday_indices`

---

## Commandes utiles

### Tests
```bash
# Test individuel
py -3 tests/test_07_market_overview.py
py -3 tests/test_08_market_overview_complete.py

# Tous les tests
py -3 tests/run_all_tests.py

# Visualiser les JSON générés
py -3 tests/view_all_results.py
```

### Scraping manuel
```bash
# Chargement initial
py -3 src/main.py

# Mise à jour quotidienne
py -3 src/main.py --daily
```

### Flows Prefect
```bash
# Chargement initial
py -3 flows/initial_load_flow.py

# Mise à jour quotidienne
py -3 flows/daily_update_flow.py

# Monitoring intraday (force hors horaires)
py -3 flows/intraday_monitoring_flow.py
```

### Infrastructure Docker
```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| Cassandra | `localhost:9042` |
| Prefect | http://localhost:4200 |
| Trino | http://localhost:8080 |
| Metabase | http://localhost:3000 |

### Variables d'environnement (`.env`)
```
CASSANDRA_HOST=localhost
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=bourse_data
CASSANDRA_STUB=false
NEXT_BUILD_ID=k6VYoXBS432b__PEHJ2s2
```

---

## Prochaines étapes

1. **Validation des données** — contrôles qualité via `DataValidator`
2. **Dashboards Metabase** — visualisation volumes, indices, top movers
3. **Analyses Big Data Trino** — requêtes SQL fédérées sur Cassandra
4. **Automatisation complète** — déploiement Prefect via `flows/deployment.yaml`
5. **Correction API index_watch** — endpoint parfois indisponible côté Bourse (fallback Next.js en place)

---

## État des composants

| Composant | Statut |
|-----------|--------|
| Scrapers (01–07) | ✅ Tests passants |
| Market overview complet | ✅ Scraper + test_08 |
| Client Cassandra | ✅ Schéma auto-créé |
| Modèles Pydantic | ✅ |
| DataValidator | ✅ |
| Flows Prefect | ✅ |
| Docker stack | ✅ Opérationnelle |
