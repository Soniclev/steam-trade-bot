from datetime import datetime

from pydantic import BaseModel

from steam_trade_bot.domain.entities.market import EntireMarketDailyStats


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
