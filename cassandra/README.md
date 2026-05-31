# Cassandra — Bourse de Casablanca

## Initialisation

Après `docker compose up -d`, attendre que Cassandra soit prête (~60 s), puis :

```bash
docker exec -it cassandra cqlsh -f /cassandra/init.cql
```

Vérification :

```bash
docker exec -it cassandra cqlsh -e "DESCRIBE TABLES;"
```

## Tables

| Table | Clé primaire | Usage reporting |
|-------|--------------|-----------------|
| `instruments_static` | `ticker` | Jointure secteur |
| `daily_prices` | `(ticker, date)` | KPIs séance, volumes |
| `historical_prices` | `(ticker, date)` | Évolutions long terme |
| `daily_indices` | `(index_name, date)` | Courbe MASI |
| `market_stats` | `date` | Volume / capi globale |
| `top_movers` | `(date, direction, rank)` | Top hausses/baisses |
| `intraday_indices` | `(index_name, date, timestamp)` | Monitoring intraday |

## Requêtes utiles

```sql
SELECT COUNT(*) FROM bourse_data.daily_prices;
SELECT * FROM bourse_data.daily_indices WHERE index_name = 'MASI' LIMIT 5;
SELECT * FROM bourse_data.market_stats LIMIT 5;
```
