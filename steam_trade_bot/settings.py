from datetime import timedelta

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class MarketItemSearchSettings(BaseSettings):
    postpone: timedelta
    retry_delay: timedelta
    max_retries: int
    workers: int

    class Config:
        env_prefix = "MARKET_ITEM_SEARCH_"
        case_sensitive = False


class MarketItemPageSettings(BaseSettings):
    postpone: timedelta
    too_many_requests_postpone: timedelta
    workers: int

    class Config:
        env_prefix = "MARKET_ITEM_PAGE_"
        case_sensitive = False


class MarketItemOrdersHistogramSettings(BaseSettings):
    postpone: timedelta
    too_many_requests_postpone: timedelta
    minimal_delay: timedelta
    timeout: timedelta
    workers: int

    class Config:
        env_prefix = "ORDERS_HISTOGRAM_"
        case_sensitive = False


class BotSettings(BaseSettings):
    database: str
    redis: str

    market_item_search = MarketItemSearchSettings()
    market_item_page = MarketItemPageSettings()
    market_item_orders = MarketItemOrdersHistogramSettings()

    min_item_price: float
    max_item_price: float

    proxy_delay: timedelta
