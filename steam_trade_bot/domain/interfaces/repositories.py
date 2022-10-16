from abc import ABC, abstractmethod

from steam_trade_bot.domain.entities.market import (
    Game,
    MarketItem,
    MarketItemSellHistory,
    SellHistoryAnalyzeResult,
)


class IGameRepository(ABC):
    @abstractmethod
    async def add(self, game: Game):
        ...

    @abstractmethod
    async def remove(self, app_id: int):
        ...

    @abstractmethod
    async def get(self, app_id: int) -> Game | None:
        ...


class IMarketItemRepository(ABC):
    @abstractmethod
    async def add(self, item: MarketItem):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str):
        ...

    @abstractmethod
    async def get(self, app_id: int, market_hash_name: str) -> MarketItem | None:
        ...


class IMarketItemSellHistoryRepository(ABC):
    @abstractmethod
    async def add(self, item: MarketItemSellHistory):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        ...

    @abstractmethod
    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> MarketItemSellHistory | None:
        ...


class ISellHistoryAnalyzeResultRepository(ABC):
    @abstractmethod
    async def add(self, item: SellHistoryAnalyzeResult):
        ...

    @abstractmethod
    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        ...

    @abstractmethod
    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> SellHistoryAnalyzeResult | None:
        ...
