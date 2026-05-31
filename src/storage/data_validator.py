# src/storage/data_validator.py
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from src.storage.models import (
    DailyIndex,
    DailyPrice,
    HistoricalPrice,
    InstrumentStatic,
    MarketStats,
    TopMover,
)
from src.utils.helpers import safe_float, safe_int
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataValidator:
    """Validation et nettoyage des données avant insertion Cassandra."""

    @staticmethod
    def _parse_french_number(value: Any) -> Optional[float]:
        if value is None or value == "" or value == "-":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = (
            str(value)
            .replace("\u00a0", "")
            .replace(" ", "")
            .replace("MAD", "")
            .replace("%", "")
            .replace("+", "")
            .replace(",", ".")
        )
        return safe_float(cleaned)

    @staticmethod
    def _parse_date(value: Any) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(str(value)[:10], fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        parsed = DataValidator._parse_french_number(value)
        if parsed is None:
            return None
        try:
            return Decimal(str(parsed))
        except InvalidOperation:
            return None

    @classmethod
    def validate_instrument_static(cls, data: Dict[str, Any]) -> Optional[InstrumentStatic]:
        try:
            return InstrumentStatic(
                ticker=str(data.get("ticker", "")).upper(),
                isin=data.get("isin"),
                sector=data.get("sector"),
                listing_date=cls._parse_date(data.get("listing_date")),
                shares_count=safe_int(data.get("shares_count")),
                nominal_value=cls._to_decimal(data.get("nominal_value")),
                trading_cycle=data.get("trading_cycle"),
                currency=data.get("currency"),
            )
        except Exception as exc:
            logger.warning(f"Validation instrument_static échouée: {exc}")
            return None

    @classmethod
    def validate_daily_price(cls, data: Dict[str, Any]) -> Optional[DailyPrice]:
        try:
            return DailyPrice(
                ticker=str(data.get("ticker", "")).upper(),
                date=cls._parse_date(data.get("date")) or date.today(),
                open_price=cls._to_decimal(data.get("open_price") or data.get("opening_price")),
                high_price=cls._to_decimal(data.get("high_price")),
                low_price=cls._to_decimal(data.get("low_price")),
                close_price=cls._to_decimal(data.get("close_price") or data.get("current_price")),
                volume=cls._to_decimal(data.get("volume")),
                quantity=safe_int(data.get("quantity")),
                trades_count=safe_int(data.get("trades_count")),
                market_cap=cls._to_decimal(data.get("market_cap")),
                variation=cls._to_decimal(data.get("variation")),
                var_ytd=cls._to_decimal(data.get("var_ytd")),
            )
        except Exception as exc:
            logger.warning(f"Validation daily_price échouée: {exc}")
            return None

    @classmethod
    def validate_historical_price(cls, data: Dict[str, Any]) -> Optional[HistoricalPrice]:
        try:
            return HistoricalPrice(
                ticker=str(data.get("ticker", "")).upper(),
                date=cls._parse_date(data.get("date")),
                open_price=cls._to_decimal(data.get("open_price")),
                high_price=cls._to_decimal(data.get("high_price")),
                low_price=cls._to_decimal(data.get("low_price")),
                close_price=cls._to_decimal(data.get("close_price")),
                volume=cls._to_decimal(data.get("volume")),
                adjusted_close=cls._to_decimal(data.get("adjusted_close")),
            )
        except Exception as exc:
            logger.warning(f"Validation historical_price échouée: {exc}")
            return None

    @classmethod
    def validate_daily_index(cls, data: Dict[str, Any]) -> Optional[DailyIndex]:
        try:
            return DailyIndex(
                index_name=str(data.get("index_name", "")),
                date=cls._parse_date(data.get("date")) or date.today(),
                value=cls._to_decimal(data.get("value")),
                variation=cls._to_decimal(data.get("variation")),
                annual_variation=cls._to_decimal(data.get("annual_variation")),
            )
        except Exception as exc:
            logger.warning(f"Validation daily_index échouée: {exc}")
            return None

    @classmethod
    def validate_market_stats(cls, data: Dict[str, Any]) -> Optional[MarketStats]:
        try:
            return MarketStats(
                date=cls._parse_date(data.get("date")) or date.today(),
                global_volume=cls._to_decimal(data.get("global_volume")),
                market_cap=cls._to_decimal(data.get("market_cap")),
            )
        except Exception as exc:
            logger.warning(f"Validation market_stats échouée: {exc}")
            return None

    @classmethod
    def validate_top_mover(cls, data: Dict[str, Any]) -> Optional[TopMover]:
        try:
            direction = data.get("direction", "up")
            if direction in ("gainer", "top_gainer"):
                direction = "up"
            elif direction in ("loser", "top_loser"):
                direction = "down"

            return TopMover(
                date=cls._parse_date(data.get("date")) or date.today(),
                direction=direction,
                rank=int(data.get("rank", 1)),
                ticker=str(data.get("ticker", "")).upper(),
                company_name=data.get("company_name") or data.get("name"),
                price=cls._to_decimal(data.get("price")),
                variation=cls._to_decimal(data.get("variation")),
            )
        except Exception as exc:
            logger.warning(f"Validation top_mover échouée: {exc}")
            return None

    @classmethod
    def validate_batch(cls, validator_name: str, records: List[Dict[str, Any]]) -> List[Any]:
        validator = getattr(cls, validator_name, None)
        if validator is None:
            raise ValueError(f"Validateur inconnu: {validator_name}")

        validated = []
        for record in records:
            item = validator(record)
            if item is not None:
                validated.append(item)
        return validated
