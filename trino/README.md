# Trino — Connecteur Cassandra

## Accès

| Contexte | URL |
|----------|-----|
| Navigateur (UI Trino) | http://localhost:8080 |
| CLI depuis l'hôte | `docker exec -it trino trino --server http://localhost:8080 --catalog cassandra --schema bourse_data` |
| JDBC (Metabase, DBeaver) | `jdbc:trino://localhost:8080/cassandra/bourse_data` |

## Catalog

Le fichier `catalog/cassandra.properties` pointe vers le service Docker `cassandra:9042`.

Les tables sont interrogées ainsi :

```sql
SELECT * FROM cassandra.bourse_data.daily_prices LIMIT 10;
```

## Requêtes KPI

Voir le dossier `sql/` pour les requêtes prêtes à l'emploi (Top volumes, secteurs, MASI, top movers).

## Metabase

Dans Metabase → Admin → Databases → Add database :

- **Type** : Trino (ou Starburst si Trino absent)
- **Host** : `trino` (depuis le container Metabase) ou `host.docker.internal` (Windows)
- **Port** : `8080`
- **Catalog** : `cassandra`
- **Schema** : `bourse_data`
- **User** : `reporting` (ou vide)
