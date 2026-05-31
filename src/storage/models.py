# src/storage/models.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InstrumentStatic(BaseModel):
    ticker: str
    isin: Optional[str] = None
    sector: Optional[str] = None
    listing_date: Optional[date] = None
    shares_count: Optional[int] = None
    nominal_value: Optional[Decimal] = None
    trading_cycle: Optional[str] = None
    currency: Optional[str] = None
    updated_at: Optional[datetime] = None


class DailyPrice(BaseModel):
    ticker: str
    date: date
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    quantity: Optional[int] = None
    trades_count: Optional[int] = None
    market_cap: Optional[Decimal] = None
    variation: Optional[Decimal] = None
    var_ytd: Optional[Decimal] = None
    scraped_at: Optional[datetime] = None


class HistoricalPrice(BaseModel):
    ticker: str
    date: date
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    updated_at: Optional[datetime] = None


class DailyIndex(BaseModel):
    index_name: str
    date: date
    value: Optional[Decimal] = None
    variation: Optional[Decimal] = None
    annual_variation: Optional[Decimal] = None
    updated_at: Optional[datetime] = None


class MarketStats(BaseModel):
    date: date
    global_volume: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    updated_at: Optional[datetime] = None


class TopMover(BaseModel):
    date: date
    direction: str = Field(pattern=r"^(up|down|gainer|loser)$")
    rank: int
    ticker: str
    company_name: Optional[str] = None
    price: Optional[Decimal] = None
    variation: Optional[Decimal] = None
    updated_at: Optional[datetime] = None

    @field_validator("direction")
    @classmethod
    def normalize_direction(cls, value: str) -> str:
        mapping = {"gainer": "up", "loser": "down", "up": "up", "down": "down"}
        return mapping.get(value.lower(), value.lower())
