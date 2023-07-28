from datetime import datetime

from pydantic import BaseModel

from steam_trade_bot.domain.entities.market import EntireMarketDailyStats
from steam_trade_bot.domain.entities.game import Game
from steam_trade_bot.type import CurrencyValue


class MarketItemSellHistoryResponse(BaseModel):
    app_id: int
    market_hash_name: str
    timestamp: datetime
    total_sold: int
    total_volume: float
    total_volume_approx_fee: float
    first_sale_datetime: datetime | None
    last_sale_datetime: datetime | None
    history: list[tuple[datetime, float, float, float, float, int]]


class EntireMarketStatsResponse(BaseModel):
    total_volume: float
    total_volume_no_fee: float
    total_volume_game_fee: float
    total_volume_steam_fee: float
    total_quantity: int
    items: list[EntireMarketDailyStats]


class MarketItemResponse(BaseModel):
    app_id: int
    market_hash_name: str
    market_fee: str | None
    market_marketable_restriction: int | None
    market_tradable_restriction: int | None
    commodity: bool

    def is_tradable(self) -> bool:
        return self.market_tradable_restriction != -1  # -1 means not tradable at all


class MarketItemsListResponse(BaseModel):
    count: int
    offset: int
    items: list[MarketItemResponse]


class GamesListResponse(BaseModel):
    count: int
    offset: int
    items: list[Game]
