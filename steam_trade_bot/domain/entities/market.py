from dataclasses import dataclass
from datetime import datetime

from steam_trade_bot.type import CurrencyValue


@dataclass
class Game:
    app_id: int
    name: str
    publisher_fee: CurrencyValue


@dataclass
class MarketItem:
    app_id: int
    market_hash_name: str
    commodity: bool
    item_name_id: int


@dataclass
class MarketItemSellHistory:
    app_id: int
    market_hash_name: str
    timestamp: datetime
    history: str


@dataclass
class BuySellItem:
    account: str
    app_id: int
    market_hash_name: str
    currency: int
    enabled: bool
    amount: int
    buy_order: CurrencyValue
    sell_order: CurrencyValue
