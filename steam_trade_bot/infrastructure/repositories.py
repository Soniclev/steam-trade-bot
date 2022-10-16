from dataclasses import asdict
from typing import Callable

from sqlalchemy import insert, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from steam_trade_bot.domain.entities.market import (
    Game,
    MarketItem,
    MarketItemSellHistory,
    SellHistoryAnalyzeResult,
)
from steam_trade_bot.domain.interfaces.repositories import (
    IGameRepository,
    IMarketItemRepository,
    IMarketItemSellHistoryRepository,
    ISellHistoryAnalyzeResultRepository,
)
from steam_trade_bot.infrastructure.models.market import (
    game_table,
    market_item_table,
    market_item_sell_history_table,
    sell_history_analyze_result_table,
)


class GameRepository(IGameRepository):
    def __init__(self, session: Callable[..., AsyncSession]):
        self._session = session

    async def add(self, game: Game):
        async with self._session() as session:
            await session.execute(insert(game_table).values(asdict(game)))
            await session.commit()

    async def remove(self, app_id: int):
        async with self._session() as session:
            await session.execute(delete(game_table).where(game_table.c.app_id == app_id))
            await session.commit()

    async def get(self, app_id: int) -> Game | None:
        async with self._session() as session:
            result = await session.execute(select(game_table).where(game_table.c.app_id == app_id))
            row = result.fetchone()
            if row:
                return Game(**row)
            else:
                return None


class MarketItemRepository(IMarketItemRepository):
    def __init__(self, session: Callable[..., AsyncSession]):
        self._session = session

    async def add(self, item: MarketItem):
        async with self._session() as session:
            await session.execute(insert(market_item_table).values(asdict(item)))
            await session.commit()

    async def remove(self, app_id: int, market_hash_name: str):
        async with self._session() as session:
            await session.execute(
                delete(market_item_table)
                .where(market_item_table.c.app_id == app_id)
                .where(market_item_table.c.market_hash_name == market_hash_name)
            )
            await session.commit()

    async def get(self, app_id: int, market_hash_name: str) -> MarketItem | None:
        async with self._session() as session:
            result = await session.execute(
                select(
                    [
                        market_item_table.c.app_id,
                        market_item_table.c.market_hash_name,
                        market_item_table.c.market_fee,
                        market_item_table.c.market_marketable_restriction,
                        market_item_table.c.market_tradable_restriction,
                        market_item_table.c.commodity,
                        market_item_table.c.item_name_id,
                    ]
                )
                .where(market_item_table.c.app_id == app_id)
                .where(market_item_table.c.market_hash_name == market_hash_name)
            )
            row = result.fetchone()
            if row:
                return MarketItem(**row)
            else:
                return None


class MarketItemSellHistoryRepository(IMarketItemSellHistoryRepository):
    def __init__(self, session: Callable[..., AsyncSession]):
        self._session = session

    async def add(self, item: MarketItemSellHistory):
        async with self._session() as session:
            await session.execute(insert(market_item_sell_history_table).values(asdict(item)))
            await session.commit()

    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        async with self._session() as session:
            await session.execute(
                delete(market_item_sell_history_table)
                .where(market_item_sell_history_table.c.app_id == app_id)
                .where(market_item_sell_history_table.c.market_hash_name == market_hash_name)
                .where(market_item_sell_history_table.c.currency == currency)
            )
            await session.commit()

    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> MarketItemSellHistory | None:
        async with self._session() as session:
            result = await session.execute(
                select(
                    [
                        market_item_sell_history_table.c.app_id,
                        market_item_sell_history_table.c.market_hash_name,
                        market_item_sell_history_table.c.currency,
                        market_item_sell_history_table.c.timestamp,
                        market_item_sell_history_table.c.history,
                    ]
                )
                .where(market_item_sell_history_table.c.app_id == app_id)
                .where(market_item_sell_history_table.c.market_hash_name == market_hash_name)
                .where(market_item_sell_history_table.c.currency == currency)
            )
            row = result.fetchone()
            if row:
                return MarketItemSellHistory(**row)
            else:
                return None


class SellHistoryAnalyzeResultRepository(ISellHistoryAnalyzeResultRepository):
    def __init__(self, session: Callable[..., AsyncSession]):
        self._session = session

    async def add(self, item: SellHistoryAnalyzeResult):
        async with self._session() as session:
            await session.execute(insert(sell_history_analyze_result_table).values(asdict(item)))
            await session.commit()

    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        async with self._session() as session:
            await session.execute(
                delete(sell_history_analyze_result_table)
                .where(sell_history_analyze_result_table.c.app_id == app_id)
                .where(sell_history_analyze_result_table.c.market_hash_name == market_hash_name)
                .where(sell_history_analyze_result_table.c.currency == currency)
            )
            await session.commit()

    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> SellHistoryAnalyzeResult | None:
        async with self._session() as session:
            result = await session.execute(
                select(
                    [
                        sell_history_analyze_result_table.c.app_id,
                        sell_history_analyze_result_table.c.market_hash_name,
                        sell_history_analyze_result_table.c.currency,
                        sell_history_analyze_result_table.c.timestamp,
                        sell_history_analyze_result_table.c.sells_last_day,
                        sell_history_analyze_result_table.c.sells_last_week,
                        sell_history_analyze_result_table.c.sells_last_month,
                        sell_history_analyze_result_table.c.recommended,
                        sell_history_analyze_result_table.c.deviation,
                        sell_history_analyze_result_table.c.sell_order,
                    ]
                )
                .where(sell_history_analyze_result_table.c.app_id == app_id)
                .where(sell_history_analyze_result_table.c.market_hash_name == market_hash_name)
                .where(sell_history_analyze_result_table.c.currency == currency)
            )
            row = result.fetchone()
            if row:
                return SellHistoryAnalyzeResult(**row)
            else:
                return None
