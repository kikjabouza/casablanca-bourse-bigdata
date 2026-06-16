# Guide de Lancement — Pipeline Big Data Bourse de Casablanca

Guide complet pour reproduire le projet de A à Z sur Windows avec Docker Desktop.

---

## Prérequis logiciels

| Outil | Version | Rôle |
|---|---|---|
| Docker Desktop | 4.x+ | Exécuter tous les conteneurs |
| Python | 3.11 ou 3.12 | Scrapers + flows (⚠ PAS 3.13 : cassandra-driver incompatible) |
| Git | Quelconque | Cloner le projet |

```powershell
# Vérifications
docker --version      # Docker version 24.x
py -3.11 --version    # Python 3.11.x
```

---

## ÉTAPE 1 — Cloner et installer les dépendances Python

```powershell
# Se placer dans le dossier du projet
cd "Projet_BD"

# Créer un environnement virtuel Python 3.11
py -3.11 -m venv venv

# Activer l'environnement
.\venv\Scripts\Activate.ps1

# Installer toutes les dépendances
pip install -r requirements.txt
```

---

## ÉTAPE 2 — Configurer les variables d'environnement

```powershell
copy .env.example .env
notepad .env
```

Paramètres essentiels dans `.env` :

```env
CASSANDRA_HOST=localhost        # depuis le PC hôte
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=bourse_data
CASSANDRA_STUB=false            # false = connexion réelle
TRACKED_INSTRUMENTS=ATW,BCP,MNG # 3 instruments suivis
PREFECT_API_URL=http://localhost:4200/api
```

> Le `scraper-worker` (Docker) utilise automatiquement `CASSANDRA_HOST=cassandra`
> via les variables d'environnement de son service — pas besoin de modifier `.env`.

---

## ÉTAPE 3 — Démarrer la stack Docker complète

```powershell
# Construire l'image du scraper-worker (première fois uniquement)
docker-compose build scraper-worker

# Démarrer tous les conteneurs
docker-compose up -d

# Vérifier l'état
docker-compose ps
```

Résultat attendu après ~2 minutes :

```
NAMES            STATUS
cassandra        Up (healthy)
trino            Up (healthy)
prefect-server   Up (healthy)
metabase         Up (healthy)
scraper-worker   Up
```

> Cassandra peut prendre 60–90 secondes à devenir `healthy`.
> Le `scraper-worker` attend automatiquement que Cassandra soit prêt.

### Services et ports exposés

| Conteneur | Port | Interface |
|---|---|---|
| Cassandra | 9042 | CQL (cqlsh) |
| Trino | 8080 (HTTP) / 8443 (HTTPS/SSL) | SQL engine |
| Prefect Server | 4200 | UI orchestration |
| Metabase | 3000 | Dashboard |

---

## ÉTAPE 4 — Vérifier que la stack fonctionne

```powershell
# Script de vérification automatique
python scripts/verify_stack.py
```

Résultat attendu :

```
[OK] Cassandra accessible (cluster: bourse-cluster)
[OK] Trino accessible (version: 426)
[OK] Prefect Server accessible -> http://localhost:4200
[OK] Metabase accessible -> http://localhost:3000
[OK] Site casablanca-bourse.com accessible
```

Vérification manuelle du schéma Cassandra :

```powershell
docker exec -it cassandra cqlsh
```

```cql
USE bourse_data;
DESCRIBE TABLES;
-- Doit afficher: instruments, instruments_static, daily_prices,
--   historical_prices, daily_indices, market_stats, top_movers, intraday_indices
```

---

## ÉTAPE 5 — Tester les scrapers (sans Cassandra)

```powershell
# Tous les tests unitaires
pytest tests/ -v

# Tests de scraping manuels (sauvegarde JSON dans tests/data/)
python tests/run_all_tests.py                  # tous
python tests/run_all_tests.py --list           # liste instruments
python tests/run_all_tests.py --overview       # market overview
python tests/run_all_tests.py --details        # détails ATW
python tests/run_all_tests.py --historical     # historique 30j ATW
```

Fichiers JSON générés dans `tests/data/` :
- `all_instruments.json` — liste complète des cotés BVC
- `ATW_details.json` — cours, volume, variation ATW
- `market_overview.json` — MASI, MASI20, top movers
- `ATW_historical_30d.json` — OHLC 30 jours

---

## ÉTAPE 6 — Chargement initial des données (1 seule fois)

```powershell
# Charger tous les instruments + 1 an d'historique OHLC pour ATW, BCP, MNG
python scripts/run_initial_load.py
```

Durée estimée : 5 à 20 minutes selon la connexion.

Puis remplir les 30 derniers jours d'indices et stats de marché :

```powershell
python scripts/backfill_indices.py
```

---

## ÉTAPE 7 — Vérifier que le scraper-worker tourne avec Prefect

Le `scraper-worker` démarre automatiquement avec `docker-compose up -d`.
Il enregistre les deployments dans Prefect et démarre le scraping.

```powershell
# Voir les logs en direct
docker logs scraper-worker --follow
```

Logs attendus :

```
Deployments enregistrés :
  → market-overview-2min  : toutes les 2 minutes
  → details-15min         : toutes les 15 minutes
Visualiser les runs : http://localhost:4200/deployments
Your deployments are being served and polling for scheduled runs!
```

Interface Prefect → http://localhost:4200
- **Deployments** : voir les 2 flows enregistrés
- **Flow Runs** : historique de chaque exécution avec statut et logs
- **Déclencher manuellement** : cliquer sur un deployment → "Run" → "Quick Run"

---

## ÉTAPE 8 — Configurer la connexion Metabase → Trino

1. Ouvrir http://localhost:3000
2. Créer un compte administrateur
3. **Ajouter une base de données** → choisir **Presto**

| Champ | Valeur |
|---|---|
| Afficher le nom | `Bourse Casablanca` |
| Hôte | `trino` |
| Port | `8443` |
| Catalog | `cassandra` |
| Schema | `bourse_data` |
| Nom d'utilisateur | `admin` |
| Mot de passe | `trino123` |
| SSL | ✅ coché |

4. Cliquer **Afficher les options avancées**
5. Dans **Additional JDBC options**, saisir **manuellement** (sans copier-coller) :
   ```
   SSLTrustStorePath=/tmp/ts.jks&SSLTrustStorePassword=changeit
   ```
6. Cliquer **Sauvegarder**

> **Pourquoi SSL ?** Trino est configuré avec HTTPS sur le port 8443 et
> un certificat auto-signé. Metabase utilise le driver JDBC Presto qui
> doit explicitement faire confiance à ce certificat via un truststore Java.

---

## ÉTAPE 9 — Créer le Dashboard Metabase

Suivre le guide détaillé : `guide_dash_metabase.md`

Résumé des 12 requêtes à créer et du layout :

**Page 1 — Vue Générale**
```
┌─────────┬──────────┬──────────┬──────────────┐
│ KPI MASI│ KPI Var% │ KPI Vol. │ KPI Capi.    │
├─────────┴──────────┴──────────┴──────────────┤
│        MASI — Évolution 30 jours (courbe)    │
├────────────────────────┬─────────────────────┤
│ Performance sectorielle│ Répartition marché  │
├────────────────────────┴─────────────────────┤
│ Top 5 Hausses          │ Top 5 Baisses       │
├─────────────────────────────────────────────┤
│         Volume quotidien 30j (courbe)        │
├─────────────────────────────────────────────┤
│         Capitalisation par secteur           │
├─────────────────────────────────────────────┤
│         Top 10 Volume du jour (tableau)      │
└─────────────────────────────────────────────┘
```

**Page 2 — Analyse par Instrument** (filtre `{{ticker}}`)
- Fiche instrument (tableau)
- Historique OHLC 90 jours (courbe)
- MASI intraday temps réel (courbe)

Activer le **rafraîchissement automatique** : icône horloge → **2 minutes**

---

## Architecture des données — Schéma Cassandra

```
instruments          → ticker, name, url, updated_at
instruments_static   → ticker, isin, sector, listing_date, shares_count,
                        nominal_value, trading_cycle, currency
daily_prices         → (ticker, date) OHLC + volume + variation + market_cap
historical_prices    → (ticker, date) OHLC ajusté, adjusted_close (ATW/BCP/MNG)
daily_indices        → (index_name, date) value + variation (MASI/MASI20/MASI_ESG)
market_stats         → date → global_volume, market_cap
top_movers           → (date, direction, rank) → top 5 hausses / top 5 baisses
intraday_indices     → (index_name, date, timestamp HH:MM) → snapshot toutes les 2 min
```

---

## Pipeline de synchronisation automatique

```
BVC (casablanca-bourse.com)
        │
        │  HTTP scraping (requests + BeautifulSoup)
        ▼
scraper-worker [Docker]
  ├── market_overview_flow  → toutes les 2 min
  │     daily_indices, market_stats, top_movers, intraday_indices
  └── details_flow          → toutes les 15 min
        daily_prices, instruments_static (ATW, BCP, MNG)
        │
        │  CQL INSERT (cassandra-driver)
        ▼
Cassandra [Docker]
        │
        │  Lecture live à chaque requête SQL (pas de cache)
        ▼
Trino [Docker]  ← moteur SQL distribué, connecteur Cassandra
        │
        │  JDBC over HTTPS (SSL)
        ▼
Metabase [Docker]  ← dashboard, refresh auto toutes les 2 min
        │
        ▼
Navigateur — Dashboard "Marché Boursier Casablanca"
```

---

## Commandes Docker utiles

```powershell
# État de tous les conteneurs
docker-compose ps

# Logs en direct
docker logs scraper-worker --follow
docker-compose logs cassandra --tail 50
docker-compose logs trino --tail 30

# Redémarrer un service
docker-compose restart scraper-worker

# Arrêter la stack (données conservées)
docker-compose down

# Arrêter ET effacer les données (ATTENTION)
docker-compose down -v

# Rebuild du worker après modification du code
docker-compose build scraper-worker && docker-compose up -d scraper-worker
```

---

## Résolution de problèmes courants

### Cassandra ne démarre pas
```powershell
docker-compose logs cassandra --tail 50
# Attendre 90s puis relancer : docker-compose restart cassandra
```

### cassandra-driver incompatible
```powershell
py --version   # Si 3.13 → utiliser py -3.11
py -3.11 -m venv venv && .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Metabase : "Authentication failed: Unauthorized"
- Vérifier que le mot de passe est `trino123` (configuré dans `trino/etc/password.db`)
- Vérifier que le port est **8443** (pas 8080)
- Vérifier que SSL est **coché**

### Metabase : "Prepared statement not found"
Cause : incompatibilité entre le driver JDBC Presto (Facebook) et Trino.
Solution déjà appliquée dans `trino/etc/config.properties` :
```properties
protocol.v1.alternate-header-name=Presto
```

### Metabase : erreur SSL / truststore
Vérifier que le JDBC option est saisi **sans espaces** :
```
SSLTrustStorePath=/tmp/ts.jks&SSLTrustStorePassword=changeit
```

### scraper-worker s'arrête immédiatement
```powershell
docker logs scraper-worker
# Si "ModuleNotFoundError: src" → rebuild : docker-compose build scraper-worker
# Si "Connection refused cassandra" → Cassandra pas encore healthy, relancer dans 30s
```

### Trino : "Column cannot be resolved" dans Metabase
- `instruments_static` n'a PAS de colonne `company_name`
- Utiliser `instruments i` (LEFT JOIN) pour récupérer `i.name AS societe`
- Voir Requête 12 dans `guide_dash_metabase.md`

### Prefect flows non visibles dans l'UI
```powershell
# Vérifier que le worker tourne
docker logs scraper-worker --tail 20
# Si pas de "Your deployments are being served" → rebuild
docker-compose build scraper-worker && docker-compose up -d scraper-worker
```
