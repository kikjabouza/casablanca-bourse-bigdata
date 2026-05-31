# Phase Analyse + Reporting

Guide pour la prochaine étape : requêtes Trino, KPIs, dashboards Metabase et rapport final.

## Prérequis

1. Stack Docker démarrée : `docker compose up -d`
2. Schéma Cassandra initialisé : voir `scripts/init_infrastructure.ps1`
3. Données chargées : `py flows/initial_load_flow.py` (ou mise à jour quotidienne)
4. Fichier `.env` configuré (copié depuis `.env.example`)

## Étape 1 — Vérifier la stack

```powershell
py -3 scripts/verify_stack.py
```

Services attendus :

| Service | URL | Rôle |
|---------|-----|------|
| Cassandra | localhost:9042 | Stockage |
| Trino | http://localhost:8080 | SQL fédéré |
| Metabase | http://localhost:3000 | Dashboards |
| Prefect | http://localhost:4200 | Orchestration |

# 1. Vérifier la stack (déjà OK chez vous)
py -3 scripts/verify_stack.py

# 2. Charger les données (si pas encore fait)
py -3 flows/initial_load_flow.py

# 3. Tester une requête Trino
# Ouvrir http://localhost:8080 → copier une requête depuis sql/queries.sql

# 4. Configurer Metabase
# http://localhost:3000 → Admin → Add database → Trino
#   Host: trino (ou host.docker.internal)
#   Port: 8080 | Catalog: cassandra | Schema: bourse_data

# 5. Créer les dashboards (voir docs/ANALYSE_REPORTING.md)

## Étape 2 — Requêtes Trino

1. Ouvrir http://localhost:8080
2. Catalog : `cassandra`, Schema : `bourse_data`
3. Copier/coller les requêtes depuis `sql/queries.sql`

CLI :

```bash
docker exec -it trino trino --server http://localhost:8080 --catalog cassandra --schema bourse_data
```

## Étape 3 — Connecter Metabase à Trino

1. Aller sur http://localhost:3000 (première visite : créer un compte admin)
2. **Admin** → **Databases** → **Add database**
3. Choisir **Trino** (ou **Starburst** si Trino n'apparaît pas)
4. Paramètres :

| Champ | Valeur |
|-------|--------|
| Display name | Bourse Casablanca |
| Host | `trino` (Metabase dans Docker) ou `host.docker.internal` (Windows) |
| Port | `8080` |
| Catalog | `cassandra` |
| Schema | `bourse_data` |
| Username | `reporting` |

5. **Save** → **Sync database schema now**

## Étape 4 — Dashboards Metabase recommandés

### Dashboard « Vue Marché » (KPIs du jour)

| Carte | Type | Requête SQL (#12) |
|-------|------|-------------------|
| Volume global | Number | `volume_global_mad` |
| Capitalisation | Number | `capitalisation_mad` |
| MASI | Number | `masi_value` + variation |
| Haussiers / Baissiers | Pie | Requête #6 |

### Dashboard « Secteurs »

| Graphique | Type | Requête |
|-----------|------|---------|
| Performance sectorielle | Bar horizontal | #2 |
| Capitalisation par secteur | Treemap | #8 |
| Top YTD par secteur | Table filtrable | #11 |

### Dashboard « Évolutions »

| Graphique | Type | Requête |
|-----------|------|---------|
| Courbe MASI / MASI20 | Line multi-série | #3 |
| Volume global 30j | Area | #9 |
| Évolution MNG (exemple) | Candlestick / Line | #7 |
| Intraday MASI | Line | #10 |

### Dashboard « Top Movers »

| Graphique | Type | Requête |
|-----------|------|---------|
| Top 5 hausses | Table | #5 (direction = up) |
| Top 5 baisses | Table | #5 (direction = down) |
| Top 10 volumes | Bar | #1 |

## Étape 5 — KPIs financiers (rapport final)

Indicateurs à documenter dans le rapport :

1. **Volume global** et **capitalisation** (market_stats)
2. **Variation MASI** journalière et YTD (daily_indices)
3. **Top 10 volumes** et **top variations** (daily_prices + top_movers)
4. **Performance sectorielle** moyenne (jointure sector)
5. **Ratio haussiers/baissers** (% valeurs en hausse)
6. **Évolution historique** d'un titre phare (historical_prices)

## Étape 6 — Présentation

Structure suggérée :

1. Contexte & architecture (pipeline Scraping → Prefect → Cassandra → Trino → Metabase)
2. Données collectées (tableau scrapers / fréquence / tables)
3. KPIs clés (captures Metabase)
4. Analyses sectorielles (charts secteurs)
5. Limites & perspectives (API Bourse, SPA, horaires marché)
6. Démonstration live (Prefect + Metabase)

## Fichiers utiles

| Fichier | Contenu |
|---------|---------|
| `sql/queries.sql` | 12 requêtes KPI prêtes |
| `cassandra/init.cql` | Schéma base |
| `trino/catalog/cassandra.properties` | Connecteur Trino |
| `.env` | Configuration locale |
| `PROJECT_STATUS.md` | État global du projet |
