from datetime import datetime
from typing import TypedDict, NamedTuple


class AppIdKey(NamedTuple):
    app_id: int


class AppIdMarketNameKey(NamedTuple):
    app_id: int
    market_hash_name: str


class GameRaw(TypedDict):
    app_id: int
    name: str


class GameStage(TypedDict):
    app_id: int
    name: str
    icon_url: str | None
    is_publisher_valve: bool


class GameDWH(GameStage):
    pass


class MarketItemRaw(TypedDict):
    app_id: int
    market_hash_name: str
    market_fee: str
    market_marketable_restriction: float
    market_tradable_restriction: float
    commodity: bool


class MarketItemStage(TypedDict):
    partition: int
    app_id: int
    market_hash_name: str
    market_fee: float
    market_marketable_restriction: float
    market_tradable_restriction: float
    commodity: bool


class MarketItemDWH(MarketItemStage):
    pass


class MarketItemSellHistoryRaw(TypedDict):
    app_id: int
    market_hash_name: str
    market_fee: str | None
    timestamp: datetime
    history: str


class MarketItemSellHistoryStage(TypedDict):
    partition: int
    app_id: int
    market_hash_name: str
    timestamp: datetime
    history: str


class MarketItemSellHistoryDWH(MarketItemSellHistoryStage):
    pass


class MarketItemStatsStage(TypedDict):
    partition: int
    app_id: int
    market_hash_name: str
    total_sold: int
    total_volume: float
    total_volume_steam_fee: float
    total_volume_publisher_fee: float
    min_price: float
    max_price: float
    first_sale_timestamp: datetime
    last_sale_timestamp: datetime


class MarketItemStatsDWH(MarketItemStatsStage):
    pass


class MarketItemOrdersRaw(TypedDict):
    partition: int
    app_id: int
    market_hash_name: str
    timestamp: datetime
    dump: str


class MarketItemOrdersStage(TypedDict):
    partition: int
    app_id: int
    market_hash_name: str
    timestamp: datetime
    buy_orders: str
    sell_orders: str


class MarketItemOrdersDWH(MarketItemOrdersStage):
    pass
