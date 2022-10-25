from datetime import timedelta

from pydantic import BaseSettings, Field


class BotSettings(BaseSettings):
    database: str
    redis: str

    min_item_price: float
    max_item_price: float

    proxy_delay: timedelta
