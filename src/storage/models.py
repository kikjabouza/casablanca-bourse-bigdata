from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime


class Instrument(BaseModel):
    ticker: str
    name: str
    url: str


class InstrumentDetails(BaseModel):
    ticker: str
    isin: Optional[str] = None
    sector: Optional[str] = None
    listing_date: Optional[str] = None
    shares_count: Optional[int] = None
    nominal_value: Optional[float] = None
    trading_cycle: Optional[str] = None
    currency: Optional[str] = None
    current_price: Optional[float] = None
    variation: Optional[float] = None
    opening_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    prev_close: Optional[float] = None
    market_cap: Optional[float] = None
    volume: Optional[float] = None
    quantity: Optional[int] = None
    trades_count: Optional[int] = None
    var_ytd: Optional[float] = None
    scraped_at: Optional[datetime] = None


class HistoricalRecord(BaseModel):
    ticker: str
    date: str
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None
    volume: Optional[float] = None
    ratio: float = 1.0

    @field_validator("ratio")
    @classmethod
    def ratio_positive(cls, v: float) -> float:
        return v if v and v > 0 else 1.0


class MarketIndex(BaseModel):
    index_name: str
    date: date
    value: float = 0.0
    variation: float = 0.0
    annual_variation: float = 0.0


class MarketStats(BaseModel):
    date: date
    global_volume: float = 0.0
    market_cap: float = 0.0


class TopMover(BaseModel):
    ticker: str
    name: str
    price: float = 0.0
    difference: float = 0.0
    variation: float = 0.0
