-- ─────────────────────────────────────────────────────────
-- BOURSE DE CASABLANCA — Requêtes Trino / KPIs Reporting
-- Catalog : cassandra  |  Schema : bourse_data
-- UI Trino : http://localhost:8080
-- ─────────────────────────────────────────────────────────

-- ============================================================
-- 1. TOP 10 VALEURS PAR VOLUME (jour le plus récent)
-- Dashboard Metabase : Bar chart
-- ============================================================
SELECT
    p.ticker,
    i.sector,
    CAST(p.close_price AS DOUBLE)   AS close_price,
    CAST(p.volume AS DOUBLE)        AS volume_mad,
    CAST(p.variation AS DOUBLE)     AS variation_pct
FROM cassandra.bourse_data.daily_prices p
LEFT JOIN cassandra.bourse_data.instruments_static i
    ON p.ticker = i.ticker
WHERE p.date = (
    SELECT MAX(date) FROM cassandra.bourse_data.daily_prices
)
ORDER BY p.volume DESC
LIMIT 10;


-- ============================================================
-- 2. PERFORMANCE SECTORIELLE (variation moyenne du jour)
-- Dashboard Metabase : Bar chart horizontal par secteur
-- ============================================================
SELECT
    COALESCE(i.sector, 'Non classé')              AS sector,
    COUNT(*)                                       AS nb_valeurs,
    ROUND(AVG(CAST(p.variation AS DOUBLE)), 2)     AS avg_variation_pct,
    ROUND(SUM(CAST(p.volume AS DOUBLE)), 0)        AS total_volume_mad
FROM cassandra.bourse_data.daily_prices p
LEFT JOIN cassandra.bourse_data.instruments_static i
    ON p.ticker = i.ticker
WHERE p.date = (
    SELECT MAX(date) FROM cassandra.bourse_data.daily_prices
)
GROUP BY 1
ORDER BY avg_variation_pct DESC;


-- ============================================================
-- 3. ÉVOLUTION MASI (30 derniers points)
-- Dashboard Metabase : Line chart (date × value)
-- ============================================================
SELECT
    date,
    index_name,
    CAST(value AS DOUBLE)           AS index_value,
    CAST(variation AS DOUBLE)       AS daily_variation_pct,
    CAST(annual_variation AS DOUBLE) AS ytd_variation_pct
FROM cassandra.bourse_data.daily_indices
WHERE index_name IN ('MASI', 'MASI20', 'MASI_ESG')
ORDER BY date DESC
LIMIT 90;


-- ============================================================
-- 4. STATISTIQUES GLOBALES DU MARCHÉ
-- Dashboard Metabase : Number cards (volume, capitalisation)
-- ============================================================
SELECT
    date,
    CAST(global_volume AS DOUBLE)   AS volume_global_mad,
    CAST(market_cap AS DOUBLE)      AS capitalisation_mad
FROM cassandra.bourse_data.market_stats
ORDER BY date DESC
LIMIT 30;


-- ============================================================
-- 5. TOP 5 HAUSSES / BAISSES DU JOUR
-- Dashboard Metabase : 2 tableaux côte à côte
-- ============================================================
SELECT
    date,
    direction,
    rank,
    ticker,
    company_name,
    CAST(price AS DOUBLE)       AS price_mad,
    CAST(variation AS DOUBLE)   AS variation_pct
FROM cassandra.bourse_data.top_movers
WHERE date = (
    SELECT MAX(date) FROM cassandra.bourse_data.top_movers
)
ORDER BY direction, rank;


-- ============================================================
-- 6. RÉPARTITION HAUSSIERS / BAISSIERS / STABLES
-- Dashboard Metabase : Pie chart
-- ============================================================
SELECT
    CASE
        WHEN CAST(variation AS DOUBLE) > 0  THEN 'Haussiers'
        WHEN CAST(variation AS DOUBLE) < 0  THEN 'Baissiers'
        ELSE 'Stables'
    END AS category,
    COUNT(*) AS nb_valeurs
FROM cassandra.bourse_data.daily_prices
WHERE date = (
    SELECT MAX(date) FROM cassandra.bourse_data.daily_prices
)
GROUP BY 1
ORDER BY nb_valeurs DESC;


-- ============================================================
-- 7. ÉVOLUTION D'UNE VALEUR (ex: MNG — MANAGEM)
-- Dashboard Metabase : Line chart OHLC
-- ============================================================
SELECT
    date,
    ticker,
    CAST(open_price AS DOUBLE)   AS open_mad,
    CAST(high_price AS DOUBLE)   AS high_mad,
    CAST(low_price AS DOUBLE)    AS low_mad,
    CAST(close_price AS DOUBLE)  AS close_mad,
    CAST(volume AS DOUBLE)       AS volume_mad,
    CAST(variation AS DOUBLE)    AS variation_pct
FROM cassandra.bourse_data.daily_prices
WHERE ticker = 'MNG'
ORDER BY date DESC
LIMIT 252;


-- ============================================================
-- 8. CAPITALISATION PAR SECTEUR
-- Dashboard Metabase : Treemap ou Bar chart
-- ============================================================
SELECT
    COALESCE(i.sector, 'Non classé') AS sector,
    COUNT(DISTINCT p.ticker)          AS nb_valeurs,
    ROUND(SUM(CAST(p.market_cap AS DOUBLE)), 0) AS capitalisation_mad
FROM cassandra.bourse_data.daily_prices p
LEFT JOIN cassandra.bourse_data.instruments_static i
    ON p.ticker = i.ticker
WHERE p.date = (
    SELECT MAX(date) FROM cassandra.bourse_data.daily_prices
)
GROUP BY 1
ORDER BY capitalisation_mad DESC;


-- ============================================================
-- 9. VOLUME GLOBAL — TENDANCE 30 JOURS
-- Dashboard Metabase : Area chart
-- ============================================================
SELECT
    date,
    CAST(global_volume AS DOUBLE) AS volume_global_mad
FROM cassandra.bourse_data.market_stats
ORDER BY date DESC
LIMIT 30;


-- ============================================================
-- 10. MONITORING INTRADAY MASI (dernière séance)
-- Dashboard Metabase : Line chart temps réel
-- ============================================================
SELECT
    index_name,
    date,
    timestamp,
    CAST(value AS DOUBLE) AS index_value
FROM cassandra.bourse_data.intraday_indices
WHERE index_name = 'MASI'
  AND date = (
      SELECT MAX(date) FROM cassandra.bourse_data.intraday_indices
      WHERE index_name = 'MASI'
  )
ORDER BY timestamp ASC
LIMIT 500;


-- ============================================================
-- 11. TOP VARIATIONS YTD PAR SECTEUR
-- Dashboard Metabase : Table + filter secteur
-- ============================================================
SELECT
    p.ticker,
    i.sector,
    CAST(p.close_price AS DOUBLE)  AS close_mad,
    CAST(p.var_ytd AS DOUBLE)       AS var_ytd_pct,
    CAST(p.market_cap AS DOUBLE)   AS market_cap_mad
FROM cassandra.bourse_data.daily_prices p
LEFT JOIN cassandra.bourse_data.instruments_static i
    ON p.ticker = i.ticker
WHERE p.date = (
    SELECT MAX(date) FROM cassandra.bourse_data.daily_prices
)
ORDER BY p.var_ytd DESC
LIMIT 20;


-- ============================================================
-- 12. VUE SYNTHÈSE — KPIs DU JOUR (1 ligne)
-- Dashboard Metabase : 4 Number cards
-- ============================================================
SELECT
    ms.date,
    CAST(ms.global_volume AS DOUBLE)                    AS volume_global_mad,
    CAST(ms.market_cap AS DOUBLE)                       AS capitalisation_mad,
    CAST(di.value AS DOUBLE)                            AS masi_value,
    CAST(di.variation AS DOUBLE)                        AS masi_variation_pct,
    (SELECT COUNT(*) FROM cassandra.bourse_data.daily_prices dp
     WHERE dp.date = ms.date)                          AS nb_cotations,
    (SELECT COUNT(*) FROM cassandra.bourse_data.daily_prices dp
     WHERE dp.date = ms.date
       AND CAST(dp.variation AS DOUBLE) > 0)            AS nb_haussiers,
    (SELECT COUNT(*) FROM cassandra.bourse_data.daily_prices dp
     WHERE dp.date = ms.date
       AND CAST(dp.variation AS DOUBLE) < 0)            AS nb_baissiers
FROM cassandra.bourse_data.market_stats ms
LEFT JOIN cassandra.bourse_data.daily_indices di
    ON di.date = ms.date AND di.index_name = 'MASI'
WHERE ms.date = (SELECT MAX(date) FROM cassandra.bourse_data.market_stats);
