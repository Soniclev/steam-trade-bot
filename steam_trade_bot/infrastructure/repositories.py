from dataclasses import asdict
from typing import Callable

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from steam_trade_bot.domain.entities.market import (
    Game,
    MarketItem,
    MarketItemSellHistory,
    SellHistoryAnalyzeResult, MarketItemInfo, MarketItemNameId,
)
from steam_trade_bot.domain.interfaces.repositories import (
    IGameRepository,
    IMarketItemRepository,
    IMarketItemSellHistoryRepository,
    ISellHistoryAnalyzeResultRepository, IMarketItemInfoRepository, IMarketItemNameIdRepository,
)
from steam_trade_bot.infrastructure.models.market import (
    game_table,
    market_item_table,
    market_item_sell_history_table,
    sell_history_analyze_result_table, market_item_info_table, market_item_name_id_table,
)


class GameRepository(IGameRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, game: Game):
        await self._session.execute(insert(game_table).values(asdict(game)))

    async def remove(self, app_id: int):
        await self._session.execute(delete(game_table).where(game_table.c.app_id == app_id))

    async def get(self, app_id: int) -> Game | None:
        result = await self._session.execute(select(game_table).where(game_table.c.app_id == app_id))
        row = result.fetchone()
        if row:
            return Game(**row)
        else:
            return None


class MarketItemInfoRepository(IMarketItemInfoRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, item: MarketItemInfo):
        await self._session.execute(insert(market_item_info_table).values(asdict(item)))

    async def add_or_update(self, item: MarketItemInfo):
        await self._session.execute(
            insert(market_item_info_table)
            .values(asdict(item))
            .on_conflict_do_update(
                constraint= market_item_info_table.primary_key,
                set_={
                    "sell_listings": item.sell_listings,
                    "sell_price": item.sell_price,
                }
            )
        )

    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        await self._session.execute(
            delete(market_item_info_table)
            .where(market_item_info_table.c.app_id == app_id)
            .where(market_item_info_table.c.market_hash_name == market_hash_name)
            .where(market_item_info_table.c.currency == currency)
        )

    async def get(self, app_id: int, market_hash_name: str, currency: int) -> MarketItemInfo | None:
        result = await self._session.execute(
            select(
                [
                    market_item_info_table.c.app_id,
                    market_item_info_table.c.market_hash_name,
                    market_item_info_table.c.currency,
                    market_item_info_table.c.sell_listings,
                    market_item_info_table.c.sell_price,
                ]
            )
            .where(market_item_info_table.c.app_id == app_id)
            .where(market_item_info_table.c.market_hash_name == market_hash_name)
            .where(market_item_info_table.c.currency == currency)
        )
        row = result.fetchone()
        if row:
            return MarketItemInfo(**row)
        else:
            return None

    async def get_all(self, app_id: int, currency: int) -> list[MarketItemInfo]:
        result = await self._session.execute(
            select(
                [
                    market_item_info_table.c.app_id,
                    market_item_info_table.c.market_hash_name,
                    market_item_info_table.c.currency,
                    market_item_info_table.c.sell_listings,
                    market_item_info_table.c.sell_price,
                ]
            )
            .where(market_item_info_table.c.app_id == app_id)
            .where(market_item_info_table.c.currency == currency)
        )
        rows = result.fetchall()
        return [MarketItemInfo(**row) for row in rows]


class MarketItemRepository(IMarketItemRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, item: MarketItem):
        await self._session.execute(insert(market_item_table).values(asdict(item)))

    async def add_or_ignore(self, item: MarketItem):
        await self._session.execute(
            insert(market_item_table)
            .values(asdict(item))
            .on_conflict_do_nothing(
                constraint=market_item_table.primary_key,
            )
        )

    async def remove(self, app_id: int, market_hash_name: str):
        await self._session.execute(
            delete(market_item_table)
            .where(market_item_table.c.app_id == app_id)
            .where(market_item_table.c.market_hash_name == market_hash_name)
        )

    async def get(self, app_id: int, market_hash_name: str) -> MarketItem | None:
        result = await self._session.execute(
            select(
                [
                    market_item_table.c.app_id,
                    market_item_table.c.market_hash_name,
                    market_item_table.c.market_fee,
                    market_item_table.c.market_marketable_restriction,
                    market_item_table.c.market_tradable_restriction,
                    market_item_table.c.commodity,
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

    async def get_all(self, app_id: int) -> list[MarketItem]:
        result = await self._session.execute(
            select(
                [
                    market_item_table.c.app_id,
                    market_item_table.c.market_hash_name,
                    market_item_table.c.market_fee,
                    market_item_table.c.market_marketable_restriction,
                    market_item_table.c.market_tradable_restriction,
                    market_item_table.c.commodity,
                ]
            )
            .where(market_item_table.c.app_id == app_id)
        )
        rows = result.fetchall()
        return [MarketItem(**row) for row in rows]


class MarketItemSellHistoryRepository(IMarketItemSellHistoryRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, item: MarketItemSellHistory):
        await self._session.execute(insert(market_item_sell_history_table).values(asdict(item)))

    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        await self._session.execute(
            delete(market_item_sell_history_table)
            .where(market_item_sell_history_table.c.app_id == app_id)
            .where(market_item_sell_history_table.c.market_hash_name == market_hash_name)
            .where(market_item_sell_history_table.c.currency == currency)
        )
    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> MarketItemSellHistory | None:
        result = await self._session.execute(
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


class MarketItemNameIdRepository(IMarketItemNameIdRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, item: MarketItemNameId):
        await self._session.execute(insert(market_item_name_id_table).values(asdict(item)))

    async def remove(self, app_id: int, market_hash_name: str):
        await self._session.execute(
            delete(market_item_name_id_table)
            .where(market_item_name_id_table.c.app_id == app_id)
            .where(market_item_name_id_table.c.market_hash_name == market_hash_name)
        )
    async def get(
        self, app_id: int, market_hash_name: str
    ) -> MarketItemNameId | None:
        result = await self._session.execute(
            select(
                [
                    market_item_name_id_table.c.app_id,
                    market_item_name_id_table.c.market_hash_name,
                    market_item_name_id_table.c.currency,
                    market_item_name_id_table.c.timestamp,
                    market_item_name_id_table.c.history,
                ]
            )
            .where(market_item_name_id_table.c.app_id == app_id)
            .where(market_item_name_id_table.c.market_hash_name == market_hash_name)
        )
        row = result.fetchone()
        if row:
            return MarketItemNameId(**row)
        else:
            return None


class SellHistoryAnalyzeResultRepository(ISellHistoryAnalyzeResultRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, item: SellHistoryAnalyzeResult):
        await self._session.execute(insert(sell_history_analyze_result_table).values(asdict(item)))

    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        await self._session.execute(
            delete(sell_history_analyze_result_table)
            .where(sell_history_analyze_result_table.c.app_id == app_id)
            .where(sell_history_analyze_result_table.c.market_hash_name == market_hash_name)
            .where(sell_history_analyze_result_table.c.currency == currency)
        )

    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> SellHistoryAnalyzeResult | None:
        result = await self._session.execute(
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
