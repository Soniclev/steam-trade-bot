import json
from datetime import datetime

from pydantic import BaseModel, validator

from steam_trade_bot.type import CurrencyValue


class MarketItem(BaseModel):
    app_id: int
    market_hash_name: str
    market_fee: str | None
    market_marketable_restriction: int | None
    market_tradable_restriction: int | None
    commodity: bool
    icon_url: str | None

    def is_tradable(self) -> bool:
        return self.market_tradable_restriction != -1  # -1 means not tradable at all


class MarketItemInfo(BaseModel):
    app_id: int
    market_hash_name: str
    sell_listings: int
    sell_price: CurrencyValue | None
    sell_price_no_fee: CurrencyValue | None


class MarketItemOrders(BaseModel):
    app_id: int
    market_hash_name: str
    timestamp: datetime
    buy_orders: list[tuple[float, int]]
    sell_orders: list[tuple[float, int]]

    @validator('buy_orders', 'sell_orders', pre=True)
    def split_str(cls, v):
        if isinstance(v, str):
            v = json.loads(v)
        return v


class MarketItemOrder(BaseModel):
    price: CurrencyValue
    quantity: int


class MarketItemNameId(BaseModel):
    app_id: int
    market_hash_name: str
    item_name_id: int


class MarketItemSellHistory(BaseModel):
    app_id: int
    market_hash_name: str
    timestamp: datetime
    history: str


class MarketItemSellHistoryStats(BaseModel):
    app_id: int
    market_hash_name: str
    total_sold: str
    total_volume: str
    total_volume_steam_fee: str
    total_volume_publisher_fee: str
    min_price: float | None
    max_price: float | None
    first_sale_timestamp: datetime | None
    last_sale_timestamp: datetime | None


class SellHistoryAnalyzeResult(BaseModel):
    app_id: int
    market_hash_name: str
    timestamp: datetime
    sells_last_day: int
    sells_last_week: int
    sells_last_month: int
    recommended: bool
    deviation: float | None
    sell_order: CurrencyValue | None
    sell_order_no_fee: CurrencyValue | None


class EntireMarketDailyStats(BaseModel):
    point_timestamp: datetime
    avg_price: float
    volume: float
    volume_no_fee: float
    volume_game_fee: float
    volume_steam_fee: float
    quantity: int
    sold_unique_items: int
