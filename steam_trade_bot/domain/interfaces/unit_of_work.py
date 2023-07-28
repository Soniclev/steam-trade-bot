from abc import ABC, abstractmethod

from steam_trade_bot.domain.interfaces.repositories import (
    IGameRepository,
    IMarketItemRepository,
    IMarketItemInfoRepository,
    IMarketItemSellHistoryRepository,
    ISellHistoryAnalyzeResultRepository,
    IMarketItemNameIdRepository,
    IMarketItemOrdersRepository, IMarketItemSellHistoryStatsRepository,
    IEntireMarketDailyStatsRepository, IAppStatsRepository,
)


class IUnitOfWork(ABC):
    game: IGameRepository
    market_item: IMarketItemRepository
    market_item_orders: IMarketItemOrdersRepository
    market_item_info: IMarketItemInfoRepository
    market_item_name_id: IMarketItemNameIdRepository
    sell_history: IMarketItemSellHistoryRepository
    sell_history_stats: IMarketItemSellHistoryStatsRepository
    sell_history_analyze_result: ISellHistoryAnalyzeResultRepository
    entire_market_daily_stats: IEntireMarketDailyStatsRepository
    app_stats: IAppStatsRepository

    @abstractmethod
    async def __aenter__(self):
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    @abstractmethod
    async def commit(self):
        ...

    @abstractmethod
    async def rollback(self):
        ...
