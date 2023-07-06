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


T = TypeVar('T')


class IAppMarketNameBasedRepositoryGeneric(ABC, Generic[T]):
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

    @abstractmethod
    async def yield_all(self, app_id: int, count: int) -> list[T]:
        ...


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


class IMarketItemRepository(IAppMarketNameBasedRepositoryGeneric[MarketItem], ABC):
    ...


class IMarketItemInfoRepository(IAppMarketNameBasedRepositoryGeneric[MarketItemInfo], ABC):
    ...


class IMarketItemOrdersRepository(IAppMarketNameBasedRepositoryGeneric[MarketItemOrders], ABC):
    ...


class IMarketItemNameIdRepository(IAppMarketNameBasedRepositoryGeneric[MarketItemNameId], ABC):
    ...


class IMarketItemSellHistoryRepository(IAppMarketNameBasedRepositoryGeneric[MarketItemSellHistory], ABC):
    ...


class IMarketItemSellHistoryStatsRepository(IAppMarketNameBasedRepositoryGeneric[MarketItemSellHistoryStats], ABC):
    ...


class ISellHistoryAnalyzeResultRepository(IAppMarketNameBasedRepositoryGeneric[SellHistoryAnalyzeResult], ABC):
    ...
