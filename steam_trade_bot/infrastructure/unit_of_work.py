from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork
from steam_trade_bot.infrastructure.repositories import GameRepository, MarketItemInfoRepository, \
    MarketItemSellHistoryRepository, SellHistoryAnalyzeResultRepository, MarketItemRepository, \
    MarketItemNameIdRepository, MarketItemOrdersRepository


class UnitOfWork(IUnitOfWork):
    def __init__(self, session_factory: Callable[..., AsyncSession]):
        self._session_factory = session_factory
        self._session = None

    async def __aenter__(self):
        self._session = self._session_factory()
        self.game = GameRepository(self._session)
        self.market_item = MarketItemRepository(self._session)
        self.market_item_orders = MarketItemOrdersRepository(self._session)
        self.market_item_info = MarketItemInfoRepository(self._session)
        self.market_item_name_id = MarketItemNameIdRepository(self._session)
        self.sell_history = MarketItemSellHistoryRepository(self._session)
        self.sell_history_analyze_result = SellHistoryAnalyzeResultRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.rollback()
        await self._session.close()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
