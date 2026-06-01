-- ─────────────────────────────────────────────────────────
-- BOURSE DE CASABLANCA — Setup Keyspace et Tables
-- Keyspace : bourse_data
-- Usage    : docker exec -it cassandra cqlsh -f /cassandra/setup_keyspace.cql
-- ─────────────────────────────────────────────────────────

CREATE KEYSPACE IF NOT EXISTS bourse_data
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE bourse_data;

-- Instruments statiques (1 ligne par ticker)
CREATE TABLE IF NOT EXISTS instruments_static (
    ticker text PRIMARY KEY,
    isin text,
    sector text,
    listing_date date,
    shares_count bigint,
    nominal_value decimal,
    trading_cycle text,
    currency text,
    updated_at timestamp
);

-- Liste des instruments (nom, URL, horodatage)
CREATE TABLE IF NOT EXISTS instruments (
    ticker text PRIMARY KEY,
    name text,
    url text,
    updated_at timestamp
);

-- Prix quotidiens de séance
CREATE TABLE IF NOT EXISTS daily_prices (
    ticker text,
    date date,
    open_price decimal,
    high_price decimal,
    low_price decimal,
    close_price decimal,
    volume decimal,
    quantity int,
    trades_count int,
    market_cap decimal,
    variation decimal,
    var_ytd decimal,
    scraped_at timestamp,
    PRIMARY KEY (ticker, date)
) WITH CLUSTERING ORDER BY (date DESC);

-- Historique long terme
CREATE TABLE IF NOT EXISTS historical_prices (
    ticker text,
    date date,
    open_price decimal,
    high_price decimal,
    low_price decimal,
    close_price decimal,
    volume decimal,
    adjusted_close decimal,
    updated_at timestamp,
    PRIMARY KEY (ticker, date)
) WITH CLUSTERING ORDER BY (date DESC);

-- Indices quotidiens (MASI, MASI20, MASI_ESG)
CREATE TABLE IF NOT EXISTS daily_indices (
    index_name text,
    date date,
    value decimal,
    variation decimal,
    annual_variation decimal,
    updated_at timestamp,
    PRIMARY KEY (index_name, date)
);

-- Statistiques globales du marché
CREATE TABLE IF NOT EXISTS market_stats (
    date date PRIMARY KEY,
    global_volume decimal,
    market_cap decimal,
    updated_at timestamp
);

-- Top 5 hausses / baisses
CREATE TABLE IF NOT EXISTS top_movers (
    date date,
    direction text,
    rank int,
    ticker text,
    company_name text,
    price decimal,
    variation decimal,
    updated_at timestamp,
    PRIMARY KEY (date, direction, rank)
);

-- Points intraday MASI (monitoring toutes les 2 min)
CREATE TABLE IF NOT EXISTS intraday_indices (
    index_name text,
    date date,
    timestamp text,
    value decimal,
    scraped_at timestamp,
    PRIMARY KEY (index_name, date, timestamp)
) WITH CLUSTERING ORDER BY (date DESC, timestamp DESC);
