from datetime import datetime

from pydantic import BaseModel


class MarketItemSellHistoryResponse(BaseModel):
    app_id: int
    market_hash_name: str
    currency: int
    timestamp: datetime
    history: list[tuple[datetime, float, int]]
