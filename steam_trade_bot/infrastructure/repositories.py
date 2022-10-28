import asyncio
from dataclasses import asdict

from asyncpg import SerializationError
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from steam_trade_bot.domain.entities.market import (
    Game,
    MarketItem,
    MarketItemSellHistory,
    SellHistoryAnalyzeResult,
    MarketItemInfo,
    MarketItemNameId,
    MarketItemOrders,
)
from steam_trade_bot.domain.interfaces.repositories import (
    IGameRepository,
    IMarketItemRepository,
    IMarketItemSellHistoryRepository,
    ISellHistoryAnalyzeResultRepository,
    IMarketItemInfoRepository,
    IMarketItemNameIdRepository,
    IMarketItemOrdersRepository,
)
from steam_trade_bot.infrastructure.models.market import (
    game_table,
    market_item_table,
    market_item_sell_history_table,
    sell_history_analyze_result_table,
    market_item_info_table,
    market_item_name_id_table,
    market_item_orders_table,
)


class GameRepository(IGameRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, game: Game):
        await self._session.execute(insert(game_table).values(asdict(game)))

    async def remove(self, app_id: int):
        await self._session.execute(delete(game_table).where(game_table.c.app_id == app_id))

    async def get(self, app_id: int) -> Game | None:
        result = await self._session.execute(
            select(game_table).where(game_table.c.app_id == app_id)
        )
        row = result.fetchone()
        if row:
            return Game(**row)
        else:
            return None

    async def get_all(self) -> list[Game]:
        result = await self._session.execute(select(game_table))
        rows = result.fetchall()
        return [Game(**row) for row in rows]


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
                constraint=market_item_info_table.primary_key,
                set_={
                    "sell_listings": item.sell_listings,
                    "sell_price": item.sell_price,
                    "sell_price_no_fee": item.sell_price_no_fee,
                },
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
                    market_item_info_table.c.sell_price_no_fee,
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
                    market_item_info_table.c.sell_price_no_fee,
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

    async def add_or_update(self, item: MarketItem):
        try:
            await self._session.execute(
                insert(market_item_table)
                .values(asdict(item))
                .on_conflict_do_update(
                    constraint=market_item_table.primary_key,
                    set_={
                        "market_fee": item.market_fee,
                        "market_marketable_restriction": item.market_marketable_restriction,
                        "market_tradable_restriction": item.market_tradable_restriction,
                        "commodity": item.commodity,
                    },
                )
            )
        except DBAPIError as exc:
            if "<class 'asyncpg.exceptions.SerializationError'>: could not serialize access due to concurrent update" in exc.args[0]:
                raise SerializationError
            raise

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
            ).where(market_item_table.c.app_id == app_id)
        )
        rows = result.fetchall()
        return [MarketItem(**row) for row in rows]


class MarketItemOrdersRepository(IMarketItemOrdersRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, item: MarketItemOrders):
        await self._session.execute(insert(market_item_orders_table).values(asdict(item)))

    async def add_or_update(self, item: MarketItemOrders):
        await self._session.execute(
            insert(market_item_orders_table)
            .values(asdict(item))
            .on_conflict_do_update(
                constraint=market_item_orders_table.primary_key,
                set_={
                    "timestamp": item.timestamp,
                    "dump": item.dump,
                    "buy_count": item.buy_count,
                    "buy_order": item.buy_order,
                    "sell_count": item.sell_count,
                    "sell_order": item.sell_order,
                    "sell_order_no_fee": item.sell_order_no_fee,
                },
            )
        )

    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        await self._session.execute(
            delete(market_item_orders_table)
            .where(market_item_orders_table.c.app_id == app_id)
            .where(market_item_orders_table.c.market_hash_name == market_hash_name)
            .where(market_item_orders_table.c.currency == currency)
        )

    async def get(
        self, app_id: int, market_hash_name: str, currency: int
    ) -> MarketItemOrders | None:
        result = await self._session.execute(
            select(
                [
                    market_item_orders_table.c.app_id,
                    market_item_orders_table.c.market_hash_name,
                    market_item_orders_table.c.currency,
                    market_item_orders_table.c.timestamp,
                    market_item_orders_table.c.dump,
                    market_item_orders_table.c.buy_count,
                    market_item_orders_table.c.buy_order,
                    market_item_orders_table.c.sell_count,
                    market_item_orders_table.c.sell_order,
                    market_item_orders_table.c.sell_order_no_fee,
                ]
            )
            .where(market_item_orders_table.c.app_id == app_id)
            .where(market_item_orders_table.c.market_hash_name == market_hash_name)
            .where(market_item_orders_table.c.currency == currency)
        )
        row = result.fetchone()
        if row:
            return MarketItemOrders(**row)
        else:
            return None


class MarketItemSellHistoryRepository(IMarketItemSellHistoryRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, item: MarketItemSellHistory):
        await self._session.execute(insert(market_item_sell_history_table).values(asdict(item)))

    async def add_or_update(self, item: MarketItemSellHistory):
        await self._session.execute(
            insert(market_item_sell_history_table)
            .values(asdict(item))
            .on_conflict_do_update(
                constraint=market_item_sell_history_table.primary_key,
                set_={
                    "timestamp": item.timestamp,
                    "history": item.history,
                },
            )
        )

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

    async def add_or_ignore(self, item: MarketItemNameId):
        await self._session.execute(
            insert(market_item_name_id_table)
            .values(asdict(item))
            .on_conflict_do_nothing(
                constraint=market_item_name_id_table.primary_key,
            )
        )

    async def remove(self, app_id: int, market_hash_name: str):
        await self._session.execute(
            delete(market_item_name_id_table)
            .where(market_item_name_id_table.c.app_id == app_id)
            .where(market_item_name_id_table.c.market_hash_name == market_hash_name)
        )

    async def get(self, app_id: int, market_hash_name: str) -> MarketItemNameId | None:
        result = await self._session.execute(
            select(
                [
                    market_item_name_id_table.c.app_id,
                    market_item_name_id_table.c.market_hash_name,
                    market_item_name_id_table.c.item_name_id,
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

    async def get_all(self, app_id: int) -> list[MarketItemNameId]:
        result = await self._session.execute(
            select(
                [
                    market_item_name_id_table.c.app_id,
                    market_item_name_id_table.c.market_hash_name,
                    market_item_name_id_table.c.item_name_id,
                ]
            ).where(market_item_name_id_table.c.app_id == app_id)
        )
        rows = result.fetchall()
        return [MarketItemNameId(**row) for row in rows]


class SellHistoryAnalyzeResultRepository(ISellHistoryAnalyzeResultRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, item: SellHistoryAnalyzeResult):
        await self._session.execute(insert(sell_history_analyze_result_table).values(asdict(item)))

    async def add_or_update(self, item: SellHistoryAnalyzeResult):
        await self._session.execute(
            insert(sell_history_analyze_result_table)
            .values(asdict(item))
            .on_conflict_do_update(
                constraint=sell_history_analyze_result_table.primary_key,
                set_={
                    "timestamp": item.timestamp,
                    "sells_last_day": item.sells_last_day,
                    "sells_last_week": item.sells_last_week,
                    "sells_last_month": item.sells_last_month,
                    "recommended": item.recommended,
                    "deviation": item.deviation,
                    "sell_order": item.sell_order,
                    "sell_order_no_fee": item.sell_order_no_fee,
                },
            )
        )

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
                    sell_history_analyze_result_table.c.sell_order_no_fee,
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
