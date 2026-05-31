# Requêtes SQL — Trino

Fichier principal : **`queries.sql`** (12 requêtes KPI)

## Exécution

- **UI Trino** : http://localhost:8080 → catalog `cassandra`, schema `bourse_data`
- **CLI** : `docker exec -it trino trino --catalog cassandra --schema bourse_data`
- **Metabase** : créer des « Questions » à partir de chaque requête

## Index des requêtes

| # | KPI | Visualisation Metabase |
|---|-----|----------------------|
| 1 | Top 10 volumes | Bar chart |
| 2 | Performance sectorielle | Bar horizontal |
| 3 | Évolution MASI | Line chart |
| 4 | Stats globales marché | Number cards |
| 5 | Top hausses / baisses | Tables |
| 6 | Répartition haussiers/baissiers | Pie chart |
| 7 | Évolution d'une valeur | Line OHLC |
| 8 | Capitalisation par secteur | Treemap |
| 9 | Volume global 30j | Area chart |
| 10 | Intraday MASI | Line temps réel |
| 11 | Top variations YTD | Table |
| 12 | Synthèse KPIs du jour | Dashboard header |

Guide complet : `docs/ANALYSE_REPORTING.md`
