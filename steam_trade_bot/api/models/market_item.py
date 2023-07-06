from datetime import datetime

from pydantic import BaseModel


class MarketItemSellHistoryResponse(BaseModel):
    app_id: int
    market_hash_name: str
    # currency: int
    timestamp: datetime
    total_sold: int
    total_volume: float
    total_volume_approx_fee: float
    first_sale_datetime: datetime | None
    last_sale_datetime: datetime | None
    history: list[tuple[datetime, float, int]]
