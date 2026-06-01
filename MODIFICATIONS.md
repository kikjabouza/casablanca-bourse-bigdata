# 📋 Documentation des Modifications - Projet Casablanca Bourse

**Date:** 2026-06-01  
**Objectif:** Restructuration du projet pour scraping complet et préparation à Cassandra + Metabase

---

## 🎯 Objectifs atteints

### 1. ✅ Suppression du scraper MASI_realtime

- **Raison:** `MarketOverviewScraper` scrape déjà tous les indices (MASI, MASI20, MASI_ESG) via la page overview
- **Fichiers supprimés:**
  - `src/scrapers/masi_realtime_scraper.py`
  - `tests/test_06_masi_realtime.py`

### 2. ✅ Nettoyage des tests

- **Philosophie:** Tests finaux validés + test global
- **Tests conservés:**
  - `tests/test_03_instruments_list_v2.py` - Liste des instruments (version finale)
  - `tests/test_04_instrument_details.py` - Détails d'un instrument
  - `tests/test_02_historical_data.py` - Données historiques (limité à 30 jours)
  - `tests/test_08_market_overview_complete.py` - Market overview complet
- **Nouveau test global:**
  - `tests/test_all_scrapers.py` - Exécute les 4 tests à la suite avec rapport
- **Tests supprimés:**
  - `test_01_get_instrument_id.py` - Obsolète
  - `test_03_instruments_list.py` - Version ancienne (remplacée par v2)
  - `test_05_full_workflow.py` - Obsolète
  - `test_06_masi_realtime.py` - Scraper supprimé
  - `test_scrapers.py` - Remplacé par test_all_scrapers.py
  - `view_all_results.py` - Utilitaire obsolète

### 3. ✅ Tests indépendants de Cassandra

- `CassandraClient` accepte le paramètre `test_mode=True` (mode test)
- **Mode test:** Stockage JSON uniquement, pas de connexion à Cassandra
- **Mode production:** Tentative de connexion réelle (test_mode=False)
- **Usage:**

  ```python
  # Tests unitaires
  cassandra = CassandraClient(test_mode=True)  # Mode JSON

  # Production
  cassandra = CassandraClient(test_mode=False) # Mode Cassandra
  ```

### 4. ✅ Préparation au stockage Cassandra

- **Nouveau dossier:** `cassandra/data/`
- **Rôle:** Stockage intermédiaire des données scrapées avant insertion dans Cassandra
- **Structure:**
  ```
  cassandra/
  ├── init.cql
  ├── README.md
  └── data/
      ├── README.md
      ├── instruments_static/
      ├── instruments_prices/
      └── market_overview/
  ```

### 5. ✅ Nettoyage du dossier scripts/

- **Supprimés:**
  - `load_data.py` - Remplacé par main.py
  - `verify_stack.py` (ancien version incomplète) - Recrée dans sa version complète
- **Conservés/Créés:**
  - `init_infrastructure.ps1` - Initialisation de la stack Docker
  - `verify_stack.py` - Vérification Cassandra/Trino/Metabase
  - `scrape.py` - Raccourci pour lancer le scraping

### 6. ✅ Main.py refactorisé

**Objectif:** Scraper TOUTES les données sans limites, sans orchestration Prefect

**Classe:** `BourseScraperOrchestrator`

**Méthodes:**

- `run_full_scraping()` - Scrape TOUTES les données
  - Liste des instruments
  - Détails de TOUS les instruments
  - Historique COMPLET de TOUS les instruments
  - Market overview complet
- `run_daily_update()` - Mise à jour quotidienne
  - Réactualise les données de séance
  - Met à jour le market overview
- `run_market_overview_only()` - Scrape uniquement l'overview
  - Indices + stats + top movers

**Usage:**

```bash
# Scraping complet (toutes les données)
python -m src.main

# Mise à jour quotidienne
python -m src.main --daily

# Market overview uniquement
python -m src.main --overview

# Ou via le script
python scripts/scrape.py [--daily | --overview]
```

---

## 📁 Structure des données

### Tests - Fichiers de résultats

```
tests/data/
├── all_instruments.json           # Liste de tous les instruments
├── MNG_details.json               # Détails d'un instrument
├── MNG_historical.json            # Données historiques
├── market_overview_complete.json  # Market overview complet
└── all_tests_results.json         # Résultats du test global
```

### Cassandra - Stockage intermédiaire

```
cassandra/data/
├── instruments_static/
│   └── [ticker]_details.json
├── instruments_prices/
│   └── [ticker]_historical.json
└── market_overview/
    └── overview_[date].json
```

---

## 🔄 Workflow complet

```
┌─────────────────────────────────────┐
│  1. Scraping (python -m src.main)   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  2. Tests unitaires (test_*.py)     │
│     Indépendants de Cassandra       │
│     Mode: JSON uniquement           │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  3. Validation (data_validator.py)  │
│     Vérifie intégrité des données   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  4. Stockage Cassandra              │
│     cassandra_client.py             │
│     Mode: Base de données réelle    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  5. Requêtes Trino + Metabase       │
│     sql/queries.sql                 │
│     Dashboards pour analyse         │
└─────────────────────────────────────┘
```

---

## 🚀 Comment tester les modifications

### Test 1: Vérifier la structure

```bash
# Vérifier que les fichiers obsolètes sont supprimés
ls src/scrapers/  # masi_realtime_scraper.py ne doit pas exister
ls tests/         # test_01, test_03, test_05, test_06, test_scrapers.py ne doivent pas exister

# Vérifier les nouveaux dossiers
ls cassandra/data/
ls scripts/
```

### Test 2: Exécuter les tests individuels

```bash
# Chaque test fonctionne indépendamment de Cassandra
python -m pytest tests/test_03_instruments_list_v2.py -v
python -m pytest tests/test_04_instrument_details.py -v
python -m pytest tests/test_02_historical_data.py -v
python -m pytest tests/test_08_market_overview_complete.py -v
```

### Test 3: Exécuter le test global

```bash
# Lance les 4 tests à la suite
python tests/test_all_scrapers.py

# Vérifie les résultats dans:
# tests/data/all_tests_results.json
```

### Test 4: Vérifier le mode test

```python
# Les données doivent être en JSON uniquement
from src.storage.cassandra_client import CassandraClient

# Mode test (défaut pour tests)
client = CassandraClient(test_mode=True)
# ✅ Pas de connexion Cassandra, données JSON

# Mode production (défaut pour main.py)
client = CassandraClient(test_mode=False)
# ✅ Tente connexion Cassandra réelle
```

### Test 5: Lancer le scraping

```bash
# Scraping complet (toutes les données)
python -m src.main
# 📊 Scrape tous les instruments + détails + historique + overview

# Mise à jour quotidienne
python -m src.main --daily
# 🔄 Réactualise les données de séance

# Market overview uniquement
python -m src.main --overview
# 🌍 Scrape indices + stats + top movers
```

### Test 6: Vérifier les résultats dans cassandra/data/

```bash
# Les fichiers JSON devraient être générés ici
ls cassandra/data/instruments_static/
ls cassandra/data/instruments_prices/
ls cassandra/data/market_overview/
```

---

## 🔧 Configuration requise

### Variables d'environnement (.env)

```env
# Cassandra
CASSANDRA_HOST=localhost
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=bourse_data

# Scraping
REQUEST_DELAY=2
BULK_REQUEST_DELAY=5
DEFAULT_START_DATE=2020-01-01

# Mode test vs production
TEST_MODE=true  # pour tests
TEST_MODE=false # pour production
```

---

## ⚙️ Intégration Prefect (à venir)

**Étapes futures:**

1. Créer workflows Prefect dans `flows/`
2. Configurer orchestration pour mises à jour automatiques
3. Intégrer `run_full_scraping()` et `run_daily_update()`
4. Gérer retry/error handling via Prefect

**Note:** Pour maintenant, utilisez `python -m src.main` directement

---

## 📊 Données scrapées

### Instruments

- **Statiques:** ISIN, secteur, date d'introduction, nominal, cycle de négociation
- **Dynamiques:** Prix de séance, volume, variation, capitalisation
- **Historiques:** Série temporelle de prix (ouverture, clôture, HAUT, BAS)

### Market Overview

- **Indices:** MASI, MASI20, MASI_ESG (valeur, variation, variation annuelle)
- **Futures:** MASI20 futures (depuis yahoo finance)
- **Statistiques:** Volume global, capitalisation totale
- **Top movers:** 5 plus fortes hausses + 5 plus fortes baisses

### Pas de redondance

- ✅ MASI_realtime supprimé (déjà dans overview)
- ✅ Tous les indices dans MarketOverviewScraper
- ✅ Données complètes sans limites artificielles

---

## 📝 Prochaines étapes

1. **Valider Cassandra:**
   - Vérifier schéma tables
   - Tester insertion données JSON
2. **Tester Trino:**
   - Requêtes sur catalogue Cassandra
   - Validation sql/queries.sql
3. **Préparer Metabase:**
   - Connecter datasource Trino
   - Créer dashboards
4. **Ajouter Prefect:**
   - Orchestration automatique
   - Mises à jour programmées
   - Gestion erreurs
5. **Livrer à l'équipe:**
   - Documentation
   - Scripts d'utilisation
   - Dashboards prêts

---

## 📞 Support

- **Scraping:** Voir `src/main.py` et `src/scrapers/`
- **Tests:** Voir `tests/test_all_scrapers.py`
- **Cassandra:** Voir `cassandra/data/README.md`
- **Logs:** Générés dans `logs/`

---

## ✨ Résumé des changements

| Aspect            | Avant                   | Après                                 |
| ----------------- | ----------------------- | ------------------------------------- |
| **MASI Realtime** | Scraper dédié           | ❌ Supprimé (overlap market_overview) |
| **Tests**         | 9 fichiers mixtes       | ✅ 4 tests finaux + 1 test global     |
| **Cassandra**     | Non disponible en test  | ✅ Mode test intégré                  |
| **Storage**       | Fichiers dispersés      | ✅ `cassandra/data/` centralisé       |
| **Scripts**       | Obsolètes               | ✅ Nettoyés et mises à jour           |
| **Main.py**       | Orchestration partielle | ✅ Scraping complet, pas de limites   |
| **Documentation** | Minimaliste             | ✅ Complete avec workflow             |
