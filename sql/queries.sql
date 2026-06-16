-- ─────────────────────────────────────────────────────────────────────────────
-- REQUÊTES TRINO — Bourse de Casablanca
-- Catalogue : cassandra
-- Schéma    : bourse_data
-- Connexion Trino UI : http://localhost:8080
-- Connexion Metabase : http://localhost:3000 (source Trino, hôte=trino, port=8080)
-- ─────────────────────────────────────────────────────────────────────────────


-- ─── 1. Top 10 instruments par volume du jour ─────────────────────────────────
-- Graphique: tableau classé
SELECT
    dp.ticker,
    ist.sector,
    dp.close_price      AS cours_cloture,
    dp.variation        AS variation_pct,
    dp.volume           AS volume_mad,
    dp.market_cap       AS capitalisation
FROM cassandra.bourse_data.daily_prices dp
LEFT JOIN cassandra.bourse_data.instruments_static ist
    ON dp.ticker = ist.ticker
WHERE dp.date = current_date
ORDER BY dp.volume DESC
LIMIT 10;


-- ─── 2. Performance sectorielle — 30 derniers jours ──────────────────────────
-- Graphique: barres (secteur vs variation moyenne)
SELECT
    ist.sector,
    ROUND(AVG(dp.variation), 2)     AS variation_moyenne_pct,
    ROUND(SUM(dp.volume) / 1e9, 2)  AS volume_total_milliards,
    COUNT(DISTINCT dp.ticker)       AS nb_instruments
FROM cassandra.bourse_data.daily_prices dp
LEFT JOIN cassandra.bourse_data.instruments_static ist
    ON dp.ticker = ist.ticker
WHERE dp.date >= DATE_ADD('day', -30, current_date)
  AND ist.sector IS NOT NULL
GROUP BY ist.sector
ORDER BY variation_moyenne_pct DESC;


-- ─── 3. Évolution du MASI — 30 derniers jours ────────────────────────────────
-- Graphique: courbe (date vs valeur MASI)
SELECT
    date,
    ROUND(value, 2)     AS valeur_masi,
    ROUND(variation, 2) AS variation_pct
FROM cassandra.bourse_data.daily_indices
WHERE index_name = 'MASI'
  AND date >= DATE_ADD('day', -30, current_date)
ORDER BY date ASC;


-- ─── 4. Statistiques globales du marché — 7 derniers jours ──────────────────
-- Graphique: KPI / tableau
SELECT
    date,
    ROUND(global_volume / 1e9, 2)  AS volume_milliards_mad,
    ROUND(market_cap / 1e9, 2)     AS capitalisation_milliards_mad
FROM cassandra.bourse_data.market_stats
ORDER BY date DESC
LIMIT 7;


-- ─── 5. Top 5 hausses du jour ─────────────────────────────────────────────────
-- Graphique: tableau
SELECT rank, ticker, company_name, price AS cours, variation AS variation_pct
FROM cassandra.bourse_data.top_movers
WHERE date = current_date
  AND direction = 'up'
ORDER BY rank ASC;


-- ─── 6. Top 5 baisses du jour ─────────────────────────────────────────────────
-- Graphique: tableau
SELECT rank, ticker, company_name, price AS cours, variation AS variation_pct
FROM cassandra.bourse_data.top_movers
WHERE date = current_date
  AND direction = 'down'
ORDER BY rank ASC;


-- ─── 7. Répartition hausses / baisses / stables du jour ──────────────────────
-- Graphique: camembert
SELECT
    COUNT(CASE WHEN variation > 0  THEN 1 END) AS en_hausse,
    COUNT(CASE WHEN variation < 0  THEN 1 END) AS en_baisse,
    COUNT(CASE WHEN variation = 0  THEN 1 END) AS stables,
    COUNT(*)                                    AS total
FROM cassandra.bourse_data.daily_prices
WHERE date = current_date;


-- ─── 8. Évolution historique OHLC — ATW (90 jours) ──────────────────────────
-- Graphique: chandelier ou courbe
SELECT
    date,
    open_price      AS ouverture,
    high_price      AS plus_haut,
    low_price       AS plus_bas,
    close_price     AS cloture,
    adjusted_close  AS cloture_ajustee,
    volume
FROM cassandra.bourse_data.historical_prices
WHERE ticker = 'ATW'
ORDER BY date DESC
LIMIT 90;


-- ─── 9. Monitoring intraday MASI — Dernier jour ──────────────────────────────
-- Graphique: courbe intraday (timestamp vs valeur)
SELECT
    timestamp,
    ROUND(value, 2) AS valeur_masi
FROM cassandra.bourse_data.intraday_indices
WHERE index_name = 'MASI'
  AND date = current_date
ORDER BY timestamp ASC;


-- ─── 10. Capitalisation par secteur — Aujourd'hui ────────────────────────────
-- Graphique: camembert ou barres horizontales
SELECT
    ist.sector,
    ROUND(SUM(dp.market_cap) / 1e9, 2) AS capitalisation_milliards,
    COUNT(DISTINCT dp.ticker)           AS nb_instruments
FROM cassandra.bourse_data.daily_prices dp
LEFT JOIN cassandra.bourse_data.instruments_static ist
    ON dp.ticker = ist.ticker
WHERE dp.date = current_date
  AND ist.sector IS NOT NULL
GROUP BY ist.sector
ORDER BY capitalisation_milliards DESC;


-- ─── 11. Tendance du volume quotidien — 30 jours ─────────────────────────────
-- Graphique: aire ou courbe (évolution du volume de marché)
SELECT
    date,
    ROUND(global_volume / 1e6, 0) AS volume_millions_mad
FROM cassandra.bourse_data.market_stats
WHERE date >= DATE_ADD('day', -30, current_date)
ORDER BY date ASC;


-- ─── 12. KPI résumé du jour (vue synthèse pour le dashboard) ─────────────────
-- Cartes KPI Metabase
SELECT
    ms.date,
    ROUND(di_masi.value, 2)         AS masi,
    ROUND(di_masi.variation, 2)     AS masi_var_pct,
    ROUND(di_m20.value, 2)          AS masi20,
    ROUND(ms.global_volume / 1e9, 2) AS volume_milliards,
    ROUND(ms.market_cap / 1e9, 2)   AS capitalisation_milliards
FROM cassandra.bourse_data.market_stats ms
LEFT JOIN cassandra.bourse_data.daily_indices di_masi
    ON ms.date = di_masi.date AND di_masi.index_name = 'MASI'
LEFT JOIN cassandra.bourse_data.daily_indices di_m20
    ON ms.date = di_m20.date AND di_m20.index_name = 'MASI20'
WHERE ms.date = current_date
LIMIT 1;

