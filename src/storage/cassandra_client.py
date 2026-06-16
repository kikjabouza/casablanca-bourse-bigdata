"""
Client Cassandra avec mode stub pour les tests.
- CASSANDRA_STUB=true  → mode test, toutes les requêtes sont des no-ops
- CASSANDRA_STUB=false → connexion réelle à Cassandra
Si cassandra-driver n'est pas installé (Python 3.13), bascule automatiquement en stub.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _dict_row_factory(colnames, rows):
    """Convertit les Row namedtuples Cassandra en dictionnaires."""
    return [dict(zip(colnames, row)) for row in rows]


class CassandraClient:
    """
    Client Cassandra dual-mode:
      - stub_mode=True  : requêtes simulées (aucune connexion), pour les tests
      - stub_mode=False : connexion réelle à Cassandra
    """

    def __init__(self, stub_mode: Optional[bool] = None):
        self.config = Config()
        self.stub_mode: bool = stub_mode if stub_mode is not None else self.config.CASSANDRA_STUB
        self.session = None
        self._cluster = None

        if not self.stub_mode:
            self._connect()

    # ─── Connexion ────────────────────────────────────────────────────────────

    def _connect(self) -> None:
        try:
            from cassandra.cluster import Cluster
            from cassandra.policies import DCAwareRoundRobinPolicy
        except ImportError:
            logger.warning(
                "cassandra-driver non disponible (incompatible Python 3.13 ?). "
                "Basculement en mode stub. Installez Python 3.11/3.12 pour la production."
            )
            self.stub_mode = True
            return

        try:
            logger.info(
                f"Connexion à Cassandra {self.config.CASSANDRA_HOST}:{self.config.CASSANDRA_PORT}..."
            )
            self._cluster = Cluster(
                contact_points=[self.config.CASSANDRA_HOST],
                port=self.config.CASSANDRA_PORT,
                connect_timeout=15,
                load_balancing_policy=DCAwareRoundRobinPolicy(local_dc="datacenter1"),
            )
            self.session = self._cluster.connect()
            self.session.row_factory = _dict_row_factory
            self._ensure_keyspace()
            logger.info("Connecte a Cassandra avec succes.")
        except Exception as exc:
            logger.warning(f"Connexion Cassandra impossible: {exc}. Mode stub active.")
            self.stub_mode = True

    def _ensure_keyspace(self) -> None:
        """Crée le keyspace si nécessaire et positionne la session dessus."""
        ks = self.config.CASSANDRA_KEYSPACE
        self.session.execute(
            f"CREATE KEYSPACE IF NOT EXISTS {ks} "
            f"WITH REPLICATION = {{'class': 'SimpleStrategy', 'replication_factor': 1}}"
        )
        self.session.set_keyspace(ks)

    # ─── Requêtes génériques ──────────────────────────────────────────────────

    def execute(self, query: str, params: tuple = ()) -> List[Dict]:
        """Exécute une requête CQL et retourne les lignes en dict."""
        if self.stub_mode:
            logger.debug(f"[STUB] {query[:120]}")
            return []
        try:
            result = self.session.execute(query, params)
            return list(result)
        except Exception as exc:
            logger.error(f"Erreur CQL: {exc}\nQuery: {query[:200]}")
            return []

    # ─── Instruments ──────────────────────────────────────────────────────────

    def get_all_instruments(self) -> Dict[str, Dict]:
        """Retourne tous les instruments existants {ticker: {name, url}}."""
        rows = self.execute("SELECT ticker, name, url FROM instruments")
        return {row["ticker"]: row for row in rows}

    def save_instrument(self, instrument: Dict) -> None:
        """Upsert un instrument dans la table instruments."""
        self.execute(
            "INSERT INTO instruments (ticker, name, url, updated_at) "
            "VALUES (%s, %s, %s, toTimestamp(now()))",
            (instrument["ticker"], instrument.get("name", ""), instrument.get("url", "")),
        )

    def save_instrument_static(self, data: Dict) -> None:
        """Upsert les informations statiques d'un instrument."""
        from datetime import datetime
        raw_date = data.get("listing_date")
        listing_date = None
        if raw_date:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    listing_date = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue
        self.execute(
            "INSERT INTO instruments_static "
            "(ticker, isin, sector, listing_date, shares_count, nominal_value, "
            "trading_cycle, currency, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))",
            (
                data.get("ticker"),
                data.get("isin"),
                data.get("sector"),
                listing_date,
                data.get("shares_count"),
                data.get("nominal_value"),
                data.get("trading_cycle"),
                data.get("currency"),
            ),
        )

    def save_daily_price(self, data: Dict) -> None:
        """Upsert les prix de séance du jour pour un instrument."""
        self.execute(
            "INSERT INTO daily_prices "
            "(ticker, date, open_price, high_price, low_price, close_price, "
            "volume, quantity, trades_count, market_cap, variation, var_ytd, scraped_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))",
            (
                data.get("ticker"),
                data.get("date"),
                data.get("opening_price"),
                data.get("high_price"),
                data.get("low_price"),
                data.get("current_price"),
                data.get("volume"),
                data.get("quantity"),
                data.get("trades_count"),
                data.get("market_cap"),
                data.get("variation"),
                data.get("var_ytd"),
            ),
        )

    def save_historical_price(self, record: Dict) -> None:
        """Upsert un enregistrement historique (OHLC + volume)."""
        ratio = record.get("ratio", 1.0) or 1.0
        close = record.get("close_price")
        adjusted_close = (close / ratio) if close else None
        self.execute(
            "INSERT INTO historical_prices "
            "(ticker, date, open_price, high_price, low_price, close_price, "
            "volume, adjusted_close, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))",
            (
                record.get("ticker"),
                record.get("date"),
                record.get("open_price"),
                record.get("high_price"),
                record.get("low_price"),
                close,
                record.get("volume"),
                adjusted_close,
            ),
        )

    # ─── Market overview ─────────────────────────────────────────────────────

    def save_daily_index(self, index_name: str, trade_date, index_data: Dict) -> None:
        self.execute(
            "INSERT INTO daily_indices "
            "(index_name, date, value, variation, annual_variation, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, toTimestamp(now()))",
            (
                index_name,
                trade_date,
                index_data.get("value"),
                index_data.get("variation"),
                index_data.get("annual_variation"),
            ),
        )

    def save_market_stats(self, trade_date, stats: Dict) -> None:
        self.execute(
            "INSERT INTO market_stats (date, global_volume, market_cap, updated_at) "
            "VALUES (%s, %s, %s, toTimestamp(now()))",
            (trade_date, stats.get("global_volume"), stats.get("market_cap")),
        )

    def save_top_mover(self, trade_date, direction: str, rank: int, mover: Dict) -> None:
        self.execute(
            "INSERT INTO top_movers "
            "(date, direction, rank, ticker, company_name, price, variation, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))",
            (
                trade_date,
                direction,
                rank,
                mover.get("ticker"),
                mover.get("name"),
                mover.get("price"),
                mover.get("variation"),
            ),
        )

    def save_intraday_index(
        self, index_name: str, trade_date, timestamp: str, value: float
    ) -> None:
        """Sauvegarde un snapshot intraday de l'indice (table intraday_indices)."""
        self.execute(
            "INSERT INTO intraday_indices "
            "(index_name, date, timestamp, value, scraped_at) "
            "VALUES (%s, %s, %s, %s, toTimestamp(now()))",
            (index_name, trade_date, timestamp, value),
        )

    # ─── Fermeture ────────────────────────────────────────────────────────────

    def close(self) -> None:
        if self._cluster and not self.stub_mode:
            self._cluster.shutdown()
            logger.info("Connexion Cassandra fermee.")
