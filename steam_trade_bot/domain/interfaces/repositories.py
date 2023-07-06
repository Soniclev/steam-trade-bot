from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from steam_trade_bot.domain.entities.market import (
    Game,
    MarketItem,
    MarketItemSellHistory,
    SellHistoryAnalyzeResult,
    MarketItemInfo,
    MarketItemNameId,
    MarketItemOrders, MarketItemSellHistoryStats,
)


class IGameRepository(ABC):
    @abstractmethod
    async def add(self, games: list[Game]):
        ...

    @abstractmethod
    async def add_or_update(self, games: list[Game]):
        ...

    @abstractmethod
    async def add_or_ignore(self, games: list[Game]):
        ...

    @abstractmethod
    async def remove(self, app_id: int):
        ...

    @abstractmethod
    async def get(self, app_id: int) -> Game | None:
        ...

    @abstractmethod
    async def get_all(self, offset: int = None, count: int = None) -> list[Game]:
        ...


class IMarketItemRepository(ABC):
    @abstractmethod
    async def add(self, items: list[MarketItem]):
        ...

    @abstractmethod
    async def add_or_update(self, items: list[MarketItem]):
        ...

    @abstractmethod
    async def add_or_ignore(self, items: list[MarketItem]):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str):
        ...

    @abstractmethod
    async def get(self, app_id: int, market_hash_name: str) -> MarketItem | None:
        ...

    @abstractmethod
    async def get_all(self, app_id: int, offset: int = None, count: int = None) -> list[MarketItem]:
        ...


class IMarketItemInfoRepository(ABC):
    @abstractmethod
    async def add(self, items: list[MarketItemInfo]):
        ...

    @abstractmethod
    async def add_or_update(self, items: list[MarketItemInfo]):
        ...

    @abstractmethod
    async def add_or_ignore(self, items: list[MarketItemInfo]):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        ...

    @abstractmethod
    async def get(self, app_id: int, market_hash_name: str, currency: int) -> MarketItemInfo | None:
        ...

    @abstractmethod
    async def get_all(self, app_id: int, currency: int, offset: int = None, count: int = None) -> list[MarketItemInfo]:
        ...


class IMarketItemOrdersRepository(ABC):
    @abstractmethod
    async def add(self, items: list[MarketItemOrders]):
        ...

    @abstractmethod
    async def add_or_update(self, items: list[MarketItemOrders]):
        ...

    @abstractmethod
    async def add_or_ignore(self, items: list[MarketItemOrders]):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        ...

    @abstractmethod
    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> MarketItemOrders | None:
        ...

    @abstractmethod
    async def get_all(
            self, app_id: int, currency: int, offset: int = None, count: int = None
    ) -> list[MarketItemOrders]:
        ...


class IMarketItemNameIdRepository(ABC):
    @abstractmethod
    async def add(self, items: list[MarketItemNameId]):
        ...

    @abstractmethod
    async def add_or_update(self, item: list[MarketItemNameId]):
        ...

    @abstractmethod
    async def add_or_ignore(self, item: list[MarketItemNameId]):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str):
        ...

    @abstractmethod
    async def get(self, app_id: int, market_hash_name: str) -> MarketItemNameId | None:
        ...

    @abstractmethod
    async def get_all(self, app_id: int, offset: int = None, count: int = None) -> list[MarketItemNameId]:
        ...


class IMarketItemSellHistoryRepository(ABC):
    @abstractmethod
    async def add(self, items: list[MarketItemSellHistory]):
        ...

    @abstractmethod
    async def add_or_update(self, items: list[MarketItemSellHistory]):
        ...

    @abstractmethod
    async def add_or_ignore(self, items: list[MarketItemSellHistory]):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        ...

    @abstractmethod
    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> MarketItemSellHistory | None:
        ...

    @abstractmethod
    async def get_all(
            self, app_id: int, currency: int, offset: int = None, count: int = None
    ) -> list[MarketItemSellHistory]:
        ...


T = TypeVar('T')


class ITestBaseGeneric(ABC, Generic[T]):
    @abstractmethod
    async def add(self, items: list[T]):
        ...

    @abstractmethod
    async def add_or_update(self, items: list[T]):
        ...

    @abstractmethod
    async def add_or_ignore(self, items: list[T]):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str):
        ...

    @abstractmethod
    async def get(
        self, app_id: int, market_hash_name: str
    ) -> T | None:
        ...

    @abstractmethod
    async def get_all(
            self, app_id: int, offset: int = None, count: int = None
    ) -> list[T]:
        ...


class IMarketItemSellHistoryStatsRepository(ITestBaseGeneric[MarketItemSellHistoryStats]):
    pass


class ISellHistoryAnalyzeResultRepository(ABC):
    @abstractmethod
    async def add(self, items: list[SellHistoryAnalyzeResult]):
        ...

    @abstractmethod
    async def add_or_update(self, items: list[SellHistoryAnalyzeResult]):
        ...

    @abstractmethod
    async def add_or_ignore(self, items: list[SellHistoryAnalyzeResult]):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        ...

    @abstractmethod
    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> SellHistoryAnalyzeResult | None:
        ...

    @abstractmethod
    async def get_all(
            self, app_id: int, currency: int, offset: int = None, count: int = None
    ) -> list[SellHistoryAnalyzeResult]:
        ...
