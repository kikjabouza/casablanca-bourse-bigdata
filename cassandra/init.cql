-- ─────────────────────────────────────────────────────────────────────────────
-- BOURSE DE CASABLANCA — Schéma Cassandra
-- Keyspace : bourse_data
-- Usage    : docker exec -it cassandra cqlsh -f /cassandra/init.cql
--            OU : python scripts/init_cassandra.py
-- ─────────────────────────────────────────────────────────────────────────────

CREATE KEYSPACE IF NOT EXISTS bourse_data
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE bourse_data;

-- ─── Table 1: Liste des instruments (tous les instruments cotés) ──────────────
-- Mise à jour: 1 fois/jour, insert si changement (ticker, name, url)
CREATE TABLE IF NOT EXISTS instruments (
    ticker      text PRIMARY KEY,
    name        text,
    url         text,
    updated_at  timestamp
);

-- ─── Table 2: Informations statiques par instrument ───────────────────────────
-- Mise à jour: toutes les 15 min (pour les 10 instruments suivis)
CREATE TABLE IF NOT EXISTS instruments_static (
    ticker          text PRIMARY KEY,
    isin            text,
    sector          text,
    listing_date    date,
    shares_count    bigint,
    nominal_value   decimal,
    trading_cycle   text,
    currency        text,
    updated_at      timestamp
);

-- ─── Table 3: Prix quotidiens de séance ──────────────────────────────────────
-- Mise à jour: toutes les 15 min (upsert du jour courant)
-- Clé de partition: ticker | Clé de clustering: date (DESC = plus récent en premier)
CREATE TABLE IF NOT EXISTS daily_prices (
    ticker          text,
    date            date,
    open_price      decimal,
    high_price      decimal,
    low_price       decimal,
    close_price     decimal,
    volume          decimal,
    quantity        int,
    trades_count    int,
    market_cap      decimal,
    variation       decimal,
    var_ytd         decimal,
    scraped_at      timestamp,
    PRIMARY KEY (ticker, date)
) WITH CLUSTERING ORDER BY (date DESC);

-- ─── Table 4: Historique long terme OHLC ─────────────────────────────────────
-- Chargement initial: 1 an complet
-- Mise à jour: 1 fois/jour (dernier jour uniquement)
-- Instruments: les 10 instruments configurés dans TRACKED_INSTRUMENTS
CREATE TABLE IF NOT EXISTS historical_prices (
    ticker          text,
    date            date,
    open_price      decimal,
    high_price      decimal,
    low_price       decimal,
    close_price     decimal,
    volume          decimal,
    adjusted_close  decimal,  -- close_price / ratio_consolide
    updated_at      timestamp,
    PRIMARY KEY (ticker, date)
) WITH CLUSTERING ORDER BY (date DESC);

-- ─── Table 5: Indices quotidiens (MASI, MASI20, MASI_ESG) ────────────────────
-- Mise à jour: toutes les 2 min (valeur du jour, écrasement de la ligne du jour)
CREATE TABLE IF NOT EXISTS daily_indices (
    index_name          text,
    date                date,
    value               decimal,
    variation           decimal,
    annual_variation    decimal,
    updated_at          timestamp,
    PRIMARY KEY (index_name, date)
) WITH CLUSTERING ORDER BY (date DESC);

-- ─── Table 6: Statistiques globales du marché ────────────────────────────────
-- Mise à jour: toutes les 2 min (volume global + capitalisation totale)
CREATE TABLE IF NOT EXISTS market_stats (
    date            date PRIMARY KEY,
    global_volume   decimal,
    market_cap      decimal,
    updated_at      timestamp
);

-- ─── Table 7: Top 5 hausses/baisses ──────────────────────────────────────────
-- Mise à jour: toutes les 2 min
-- direction: 'up' (hausses) ou 'down' (baisses)
-- rank: 1 à 5
CREATE TABLE IF NOT EXISTS top_movers (
    date            date,
    direction       text,
    rank            int,
    ticker          text,
    company_name    text,
    price           decimal,
    variation       decimal,
    updated_at      timestamp,
    PRIMARY KEY (date, direction, rank)
);

-- ─── Table 8: Snapshots intraday des indices ──────────────────────────────────
-- Mise à jour: toutes les 2 min (1 nouvelle ligne à chaque exécution)
-- timestamp: format HH:MM (ex: '09:30', '09:32', ..., '17:58')
-- Permet de tracer la courbe intraday du MASI dans Metabase
CREATE TABLE IF NOT EXISTS intraday_indices (
    index_name  text,
    date        date,
    timestamp   text,
    value       decimal,
    scraped_at  timestamp,
    PRIMARY KEY (index_name, date, timestamp)
) WITH CLUSTERING ORDER BY (date DESC, timestamp DESC);
