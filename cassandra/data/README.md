# cassandra/data - Résultats du Scraping

Ce dossier stocke les résultats du scraping en format JSON en attente d'insertion dans Cassandra.

## Structure

- `instruments_static/` - Données statiques des instruments (détails)
- `instruments_prices/` - Données historiques de prix
- `market_overview/` - Données du market overview (indices, stats, top movers)

## Format des fichiers

Chaque fichier JSON contient:
- Les données scrapées du Casablanca Bourse
- Métadonnées (date de scraping, etc.)

## Mode opératoire

1. **Scraping** - `python -m src.main` scrape les données et les stocke ici
2. **Validation** - `data_validator.py` valide les données avant insertion
3. **Insertion** - `cassandra_client.py` insère dans la base de données
4. **Requêtes** - `sql/queries.sql` permet de consulter les données

## Workflow

```
main.py (scraping)
    ↓
cassandra/data/ (stockage JSON)
    ↓
data_validator.py (validation)
    ↓
cassandra_client.py (insertion DB)
    ↓
Cassandra (stockage permanent)
```

## Notes

- Les fichiers JSON sont générés dynamiquement à chaque scraping
- Cassandra stocke les données de manière permanente
- SQL/Metabase accèdent aux données via Cassandra
- Prefect orchestrera les mises à jour automatiques (à venir)

Voir aussi: [MODIFICATIONS.md](../../MODIFICATIONS.md)
