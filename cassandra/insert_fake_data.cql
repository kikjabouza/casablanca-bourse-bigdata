-- ─────────────────────────────────────────────────────────
-- BOURSE DE CASABLANCA — Insertion de Données FAKE
-- Keyspace : bourse_data
-- Usage    : docker exec -it cassandra cqlsh -f /cassandra/insert_fake_data.cql
-- ─────────────────────────────────────────────────────────

USE bourse_data;

-- ─────────────────────────────────────────────────────────
-- TABLE: instruments (Liste des instruments)
-- ─────────────────────────────────────────────────────────
INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('MNG', 'MANAGEM', '/fr/live-market/instruments/MNG', '2026-06-01 19:44:24');

INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('BOA', 'BANK OF AFRICA', '/fr/live-market/instruments/BOA', '2026-06-01 19:44:24');

INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('ATW', 'ATTIJARIWAFA BANK', '/fr/live-market/instruments/ATW', '2026-06-01 19:44:24');

INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('BCP', 'BCP', '/fr/live-market/instruments/BCP', '2026-06-01 19:44:24');

INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('IAM', 'IAM', '/fr/live-market/instruments/IAM', '2026-06-01 19:44:24');

INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('OCP', 'OCP GROUP', '/fr/live-market/instruments/OCP', '2026-06-01 19:44:24');

INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('MSA', 'SODEP-Marsa Maroc', '/fr/live-market/instruments/MSA', '2026-06-01 19:44:24');

INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('LBV', 'LABEL VIE', '/fr/live-market/instruments/LBV', '2026-06-01 19:44:24');

INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('ADI', 'ALLIANCES', '/fr/live-market/instruments/ADI', '2026-06-01 19:44:24');

INSERT INTO instruments (ticker, name, url, updated_at) 
VALUES ('SONASID', 'SONASID', '/fr/live-market/instruments/SID', '2026-06-01 19:44:24');

-- ─────────────────────────────────────────────────────────
-- TABLE: instruments_static (Détails statiques des instruments)
-- ─────────────────────────────────────────────────────────
INSERT INTO instruments_static (ticker, isin, sector, listing_date, shares_count, nominal_value, trading_cycle, currency, updated_at) 
VALUES ('MNG', 'MA0000011058', 'Mines', '2000-07-11', 11864676, 100.0, 'Groupe 1', 'Dirham marocain', '2026-06-01 19:44:24');

INSERT INTO instruments_static (ticker, isin, sector, listing_date, shares_count, nominal_value, trading_cycle, currency, updated_at) 
VALUES ('BOA', 'MA0000011170', 'Banques', '2004-03-31', 50000000, 100.0, 'Groupe 1', 'Dirham marocain', '2026-06-01 19:44:24');

INSERT INTO instruments_static (ticker, isin, sector, listing_date, shares_count, nominal_value, trading_cycle, currency, updated_at) 
VALUES ('ATW', 'MA0000011185', 'Banques', '2004-06-30', 75000000, 100.0, 'Groupe 1', 'Dirham marocain', '2026-06-01 19:44:24');

INSERT INTO instruments_static (ticker, isin, sector, listing_date, shares_count, nominal_value, trading_cycle, currency, updated_at) 
VALUES ('BCP', 'MA0000011190', 'Banques', '2004-09-30', 100000000, 100.0, 'Groupe 1', 'Dirham marocain', '2026-06-01 19:44:24');

INSERT INTO instruments_static (ticker, isin, sector, listing_date, shares_count, nominal_value, trading_cycle, currency, updated_at) 
VALUES ('IAM', 'MA0000011200', 'Télécom', '2005-01-15', 200000000, 10.0, 'Groupe 1', 'Dirham marocain', '2026-06-01 19:44:24');

-- ─────────────────────────────────────────────────────────
-- TABLE: daily_prices (Prix quotidiens de séance)
-- ─────────────────────────────────────────────────────────
INSERT INTO daily_prices (ticker, date, open_price, high_price, low_price, close_price, volume, quantity, trades_count, market_cap, variation, var_ytd, scraped_at) 
VALUES ('MNG', '2026-06-01', 17927.0, 18894.0, 17500.0, 18098.0, 53347361.0, 2949, 323, 214726906248.0, 3.98, 182.78, '2026-06-01 19:44:24');

INSERT INTO daily_prices (ticker, date, open_price, high_price, low_price, close_price, volume, quantity, trades_count, market_cap, variation, var_ytd, scraped_at) 
VALUES ('MNG', '2026-05-31', 17405.0, 17600.0, 17300.0, 17405.0, 45000000.0, 2500, 280, 206500000000.0, 2.5, 178.5, '2026-05-31 19:44:24');

INSERT INTO daily_prices (ticker, date, open_price, high_price, low_price, close_price, volume, quantity, trades_count, market_cap, variation, var_ytd, scraped_at) 
VALUES ('MNG', '2026-05-30', 17000.0, 17500.0, 16800.0, 17000.0, 38000000.0, 2200, 250, 201700000000.0, -1.2, 175.0, '2026-05-30 19:44:24');

INSERT INTO daily_prices (ticker, date, open_price, high_price, low_price, close_price, volume, quantity, trades_count, market_cap, variation, var_ytd, scraped_at) 
VALUES ('BOA', '2026-06-01', 450.0, 460.0, 445.0, 455.0, 15000000.0, 35000, 450, 22750000000.0, 1.5, 25.3, '2026-06-01 19:44:24');

INSERT INTO daily_prices (ticker, date, open_price, high_price, low_price, close_price, volume, quantity, trades_count, market_cap, variation, var_ytd, scraped_at) 
VALUES ('ATW', '2026-06-01', 690.0, 705.0, 685.0, 698.0, 25000000.0, 36000, 520, 52350000000.0, 2.1, 18.7, '2026-06-01 19:44:24');

INSERT INTO daily_prices (ticker, date, open_price, high_price, low_price, close_price, volume, quantity, trades_count, market_cap, variation, var_ytd, scraped_at) 
VALUES ('BCP', '2026-06-01', 230.0, 240.0, 228.0, 236.0, 18000000.0, 78000, 650, 23600000000.0, 3.5, 12.4, '2026-06-01 19:44:24');

INSERT INTO daily_prices (ticker, date, open_price, high_price, low_price, close_price, volume, quantity, trades_count, market_cap, variation, var_ytd, scraped_at) 
VALUES ('IAM', '2026-06-01', 8.5, 8.8, 8.4, 8.7, 35000000.0, 4000000, 1200, 17400000000.0, 1.2, -5.3, '2026-06-01 19:44:24');

INSERT INTO daily_prices (ticker, date, open_price, high_price, low_price, close_price, volume, quantity, trades_count, market_cap, variation, var_ytd, scraped_at) 
VALUES ('MSA', '2026-06-01', 1250.0, 1280.0, 1240.0, 1270.0, 8500000.0, 6700, 180, 12700000000.0, 2.8, 15.6, '2026-06-01 19:44:24');

-- ─────────────────────────────────────────────────────────
-- TABLE: historical_prices (Historique long terme)
-- ─────────────────────────────────────────────────────────
INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('MNG', '2026-04-01', 8598.0, 9349.0, 8540.0, 9349.0, 95803437.0, 9349.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('MNG', '2026-04-15', 14390.0, 14400.0, 12905.0, 13500.0, 94277929.0, 13500.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('MNG', '2026-05-01', 13713.0, 14000.0, 13712.0, 13900.0, 7791522.0, 13900.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('MNG', '2026-05-15', 14700.0, 15350.0, 14000.0, 14000.0, 96325279.0, 14000.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('MNG', '2026-06-01', 17927.0, 18894.0, 17500.0, 18098.0, 53347361.0, 18098.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('BOA', '2026-04-01', 380.0, 400.0, 375.0, 395.0, 12000000.0, 395.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('BOA', '2026-05-01', 420.0, 435.0, 415.0, 430.0, 14000000.0, 430.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('BOA', '2026-06-01', 450.0, 460.0, 445.0, 455.0, 15000000.0, 455.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('ATW', '2026-04-01', 580.0, 600.0, 575.0, 595.0, 20000000.0, 595.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('ATW', '2026-05-01', 650.0, 670.0, 645.0, 665.0, 22000000.0, 665.0, '2026-06-01 19:44:24');

INSERT INTO historical_prices (ticker, date, open_price, high_price, low_price, close_price, volume, adjusted_close, updated_at) 
VALUES ('ATW', '2026-06-01', 690.0, 705.0, 685.0, 698.0, 25000000.0, 698.0, '2026-06-01 19:44:24');

-- ─────────────────────────────────────────────────────────
-- TABLE: daily_indices (Indices quotidiens)
-- ─────────────────────────────────────────────────────────
INSERT INTO daily_indices (index_name, date, value, variation, annual_variation, updated_at) 
VALUES ('MASI', '2026-06-01', 19048.6726, 0.0, 0.0, '2026-06-01 19:44:26');

INSERT INTO daily_indices (index_name, date, value, variation, annual_variation, updated_at) 
VALUES ('MASI20', '2026-06-01', 18985.9703, 0.0, 0.0, '2026-06-01 19:44:26');

INSERT INTO daily_indices (index_name, date, value, variation, annual_variation, updated_at) 
VALUES ('MASI_ESG', '2026-06-01', 18985.9703, 0.0, 0.0, '2026-06-01 19:44:26');

INSERT INTO daily_indices (index_name, date, value, variation, annual_variation, updated_at) 
VALUES ('MASI', '2026-05-31', 18980.5432, 0.5, 8.5, '2026-05-31 19:44:26');

INSERT INTO daily_indices (index_name, date, value, variation, annual_variation, updated_at) 
VALUES ('MASI20', '2026-05-31', 18920.1234, 0.4, 7.8, '2026-05-31 19:44:26');

INSERT INTO daily_indices (index_name, date, value, variation, annual_variation, updated_at) 
VALUES ('MASI', '2026-05-30', 18870.9876, -0.3, 7.2, '2026-05-30 19:44:26');

INSERT INTO daily_indices (index_name, date, value, variation, annual_variation, updated_at) 
VALUES ('MASI', '2026-05-01', 18500.0000, 1.2, 5.5, '2026-05-01 19:44:26');

INSERT INTO daily_indices (index_name, date, value, variation, annual_variation, updated_at) 
VALUES ('MASI', '2026-04-01', 17800.0000, 0.8, 3.2, '2026-04-01 19:44:26');

-- ─────────────────────────────────────────────────────────
-- TABLE: market_stats (Statistiques globales du marché)
-- ─────────────────────────────────────────────────────────
INSERT INTO market_stats (date, global_volume, market_cap, updated_at) 
VALUES ('2026-06-01', 360500768.0, 1105581666713.0, '2026-06-01 19:44:26');

INSERT INTO market_stats (date, global_volume, market_cap, updated_at) 
VALUES ('2026-05-31', 340000000.0, 1095000000000.0, '2026-05-31 19:44:26');

INSERT INTO market_stats (date, global_volume, market_cap, updated_at) 
VALUES ('2026-05-30', 320000000.0, 1082000000000.0, '2026-05-30 19:44:26');

INSERT INTO market_stats (date, global_volume, market_cap, updated_at) 
VALUES ('2026-05-01', 280000000.0, 1050000000000.0, '2026-05-01 19:44:26');

INSERT INTO market_stats (date, global_volume, market_cap, updated_at) 
VALUES ('2026-04-01', 250000000.0, 1020000000000.0, '2026-04-01 19:44:26');

-- ─────────────────────────────────────────────────────────
-- TABLE: top_movers (Top 5 hausses / baisses)
-- ─────────────────────────────────────────────────────────
INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'up', 1, 'MNG', 'MANAGEM', 18098.0, 3.98, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'up', 2, 'ATW', 'ATTIJARIWAFA BANK', 698.0, 2.1, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'up', 3, 'BCP', 'BCP', 236.0, 3.5, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'up', 4, 'MSA', 'SODEP-Marsa Maroc', 1270.0, 2.8, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'up', 5, 'BOA', 'BANK OF AFRICA', 455.0, 1.5, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'down', 1, 'IAM', 'IAM', 8.7, -2.5, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'down', 2, 'LBV', 'LABEL VIE', 850.0, -1.8, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'down', 3, 'ADI', 'ALLIANCES', 389.0, -1.2, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'down', 4, 'SONASID', 'SONASID', 450.0, -0.9, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-06-01', 'down', 5, 'OCP', 'OCP GROUP', 1200.0, -0.5, '2026-06-01 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-05-31', 'up', 1, 'MNG', 'MANAGEM', 17405.0, 2.5, '2026-05-31 19:44:26');

INSERT INTO top_movers (date, direction, rank, ticker, company_name, price, variation, updated_at) 
VALUES ('2026-05-31', 'up', 2, 'ATW', 'ATTIJARIWAFA BANK', 685.0, 1.8, '2026-05-31 19:44:26');

-- ─────────────────────────────────────────────────────────
-- TABLE: intraday_indices (Points intraday MASI)
-- ─────────────────────────────────────────────────────────
INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:00:00', 19000.0, '2026-06-01 09:00:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:02:00', 19005.5, '2026-06-01 09:02:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:04:00', 19010.2, '2026-06-01 09:04:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:06:00', 19015.8, '2026-06-01 09:06:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:08:00', 19020.3, '2026-06-01 09:08:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:10:00', 19025.1, '2026-06-01 09:10:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:12:00', 19030.5, '2026-06-01 09:12:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:14:00', 19035.2, '2026-06-01 09:14:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:16:00', 19040.8, '2026-06-01 09:16:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI', '2026-06-01', '09:18:00', 19045.3, '2026-06-01 09:18:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI20', '2026-06-01', '09:00:00', 18940.0, '2026-06-01 09:00:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI20', '2026-06-01', '09:02:00', 18945.2, '2026-06-01 09:02:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI20', '2026-06-01', '09:04:00', 18950.5, '2026-06-01 09:04:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI20', '2026-06-01', '09:06:00', 18955.8, '2026-06-01 09:06:00');

INSERT INTO intraday_indices (index_name, date, timestamp, value, scraped_at) 
VALUES ('MASI20', '2026-06-01', '09:08:00', 18960.3, '2026-06-01 09:08:00');
