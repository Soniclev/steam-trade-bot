import operator
from dataclasses import asdict
from datetime import datetime
from typing import TypeVar, Generic

from steam_trade_bot.domain.exceptions import SerializationError
from sqlalchemy import delete, select, Table
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

T = TypeVar('T')


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, table: Table, on_conflict_update: set[str],
                 type_: type):
        self._session = session
        self._table = table
        self._conflict_update_set = {x: operator.attrgetter(x) for x in on_conflict_update}
        self._type = type_

    async def add(self, items: list[T]):
        try:
            stmt = insert(self._table) \
                .values([asdict(item) for item in items])
            await self._session.execute(stmt)
        except DBAPIError as exc:
            if "<class 'asyncpg.exceptions.SerializationError'>: could not serialize access due to concurrent update" in \
                    exc.args[0]:
                raise SerializationError from exc
            raise

    async def add_or_update(self, items: list[T]):
        try:
            stmt = insert(self._table) \
                .values([asdict(item) for item in items])
            set_ = {
                key: value(stmt.excluded)
                for key, value in self._conflict_update_set.items()
            }
            stmt = stmt.on_conflict_do_update(
                constraint=self._table.primary_key,
                set_=set_
            )
            await self._session.execute(stmt)
        except DBAPIError as exc:
            if "<class 'asyncpg.exceptions.SerializationError'>: could not serialize access due to concurrent update" in \
                    exc.args[0]:
                raise SerializationError from exc
            raise

    async def add_or_ignore(self, items: list[T]):
        try:
            stmt = insert(self._table) \
                .values([asdict(item) for item in items])
            stmt = stmt.on_conflict_do_nothing(
                constraint=self._table.primary_key
            )
            await self._session.execute(stmt)
        except DBAPIError as exc:
            if "<class 'asyncpg.exceptions.SerializationError'>: could not serialize access due to concurrent update" in \
                    exc.args[0]:
                raise SerializationError from exc
            raise

    async def _remove(self, stmt):
        await self._session.execute(stmt)

    async def _get(self, stmt) -> T | None:
        result = await self._session.execute(stmt)
        row = result.fetchone()
        if row:
            return self._type(**row)
        else:
            return None

    async def _get_all(self, stmt) -> list[T]:
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        return [self._type(**row) for row in rows]


class AppCurrencyBasedRepository(BaseRepository[T]):
    def __init__(self, session: AsyncSession, table: Table, on_conflict_update: set[str],
                 select_: list, type_: type):
        super().__init__(session, table, on_conflict_update, type_)
        self._select = select_

    async def remove(self, app_id: int, market_hash_name: str, currency: int):
        await super(AppCurrencyBasedRepository, self)._remove(
            delete(self._table)
            .where(self._table.c.app_id == app_id)
            .where(self._table.c.market_hash_name == market_hash_name)
            .where(self._table.c.currency == currency)
        )

    async def get(
            self, app_id: int, market_hash_name: str, currency: int
    ) -> T | None:
        return await super(AppCurrencyBasedRepository, self)._get(
            select(self._select)
            .where(self._table.c.app_id == app_id)
            .where(self._table.c.market_hash_name == market_hash_name)
            .where(self._table.c.currency == currency)
        )

    async def get_all(
            self, app_id: int, currency: int, offset: int = None, count: int = None
    ) -> list[T]:
        stmt = select(self._select) \
            .where(self._table.c.app_id == app_id) \
            .where(self._table.c.currency == currency)
        if count:
            stmt = stmt.limit(count)
        if offset:
            stmt = stmt.offset(offset)
        return await super(AppCurrencyBasedRepository, self)._get_all(stmt)


class GameRepository(BaseRepository[Game], IGameRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, game_table, {"name"}, Game)

    async def remove(self, app_id: int):
        await super(GameRepository).remove(
            delete(self._table).where(self._table.c.app_id == app_id)
        )

    async def get(self, app_id: int) -> Game | None:
        return await super(GameRepository).get(
            select(self._table).where(self._table.c.app_id == app_id)
        )

    async def get_all(self, offset: int = None, count: int = None) -> list[Game]:
        stmt = select(self._table)
        if offset:
            stmt = stmt.offset(offset)
        if count:
            stmt = stmt.limit(count)
        return await super(GameRepository, self)._get_all(stmt)


class MarketItemInfoRepository(AppCurrencyBasedRepository[MarketItemInfo],
                               IMarketItemInfoRepository):
    def __init__(self, session: AsyncSession):
        super(MarketItemInfoRepository, self).__init__(
            session, market_item_info_table,
            {"sell_listings", "sell_price",
             "sell_price_no_fee"},
            [
                market_item_info_table.c.app_id,
                market_item_info_table.c.market_hash_name,
                market_item_info_table.c.currency,
                market_item_info_table.c.sell_listings,
                market_item_info_table.c.sell_price,
                market_item_info_table.c.sell_price_no_fee,
            ],
            MarketItemInfo
        )


class MarketItemRepository(BaseRepository[MarketItem], IMarketItemRepository):
    def __init__(self, session: AsyncSession):
        super(MarketItemRepository, self).__init__(session, market_item_table,
                                                   {"market_fee", "market_marketable_restriction",
                                                    "market_tradable_restriction", "commodity"},
                                                   MarketItem)
        self._select = [
            market_item_table.c.app_id,
            market_item_table.c.market_hash_name,
            market_item_table.c.market_fee,
            market_item_table.c.market_marketable_restriction,
            market_item_table.c.market_tradable_restriction,
            market_item_table.c.commodity,
        ]

    async def remove(self, app_id: int, market_hash_name: str):
        await super(MarketItemRepository, self)._remove(
            delete(market_item_table)
            .where(market_item_table.c.app_id == app_id)
            .where(market_item_table.c.market_hash_name == market_hash_name)
        )

    async def get(self, app_id: int, market_hash_name: str) -> MarketItem | None:
        return await super(MarketItemRepository, self)._get(
            select(self._select)
            .where(market_item_table.c.app_id == app_id)
            .where(market_item_table.c.market_hash_name == market_hash_name)
        )

    async def get_all(self, app_id: int, offset: int = None, count: int = None) -> list[MarketItem]:
        stmt = select(self._select).where(market_item_table.c.app_id == app_id)
        if offset:
            stmt = stmt.offset(offset)
        if count:
            stmt = stmt.limit(count)
        return await super(MarketItemRepository, self)._get_all(stmt)


class MarketItemOrdersRepository(AppCurrencyBasedRepository[MarketItemOrders],
                                 IMarketItemOrdersRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        super(MarketItemOrdersRepository, self).__init__(
            session, market_item_orders_table,
            {"timestamp", "dump", "buy_count",
             "buy_order", "sell_count", "sell_order",
             "sell_order_no_fee"}, [
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
            ],
            MarketItemOrders
        )

    async def yield_all(self, app_id: int, currency: int, count: int) -> list[MarketItemOrders]:
        stmt = select(self._select)\
            .where(market_item_orders_table.c.app_id == app_id)\
            .where(market_item_orders_table.c.currency == currency)

        async_result = await self._session.stream(stmt)

        while rows := await async_result.fetchmany(count):
            yield [MarketItemOrders(**row) for row in rows]


class MarketItemSellHistoryRepository(AppCurrencyBasedRepository[MarketItemSellHistory],
                                      IMarketItemSellHistoryRepository):
    def __init__(self, session: AsyncSession):
        super(MarketItemSellHistoryRepository, self).__init__(
            session,
            market_item_sell_history_table,
            {"timestamp", "history"}, [
                market_item_sell_history_table.c.app_id,
                market_item_sell_history_table.c.market_hash_name,
                market_item_sell_history_table.c.currency,
                market_item_sell_history_table.c.timestamp,
                market_item_sell_history_table.c.history,
            ],
            MarketItemSellHistory
        )


class MarketItemNameIdRepository(BaseRepository[MarketItemNameId], IMarketItemNameIdRepository):
    def __init__(self, session: AsyncSession):
        super(MarketItemNameIdRepository, self).__init__(
            session, market_item_name_id_table,
            {"item_name_id"},
            MarketItemNameId
        )
        self._select = [
            market_item_name_id_table.c.app_id,
            market_item_name_id_table.c.market_hash_name,
            market_item_name_id_table.c.item_name_id,
        ]

    async def remove(self, app_id: int, market_hash_name: str):
        await super(MarketItemNameIdRepository, self)._remove(
            delete(market_item_name_id_table)
            .where(market_item_name_id_table.c.app_id == app_id)
            .where(market_item_name_id_table.c.market_hash_name == market_hash_name)
        )

    async def get(self, app_id: int, market_hash_name: str) -> MarketItemNameId | None:
        return await super(MarketItemNameIdRepository, self)._get(
            select(
                self._select
            )
            .where(market_item_name_id_table.c.app_id == app_id)
            .where(market_item_name_id_table.c.market_hash_name == market_hash_name)
        )

    async def get_all(self, app_id: int, offset: int = None, count: int = None) -> list[
        MarketItemNameId]:
        stmt = select(self._select).where(market_item_name_id_table.c.app_id == app_id)
        if offset:
            stmt = stmt.offset(offset)
        if count:
            stmt = stmt.limit(count)
        return await super(MarketItemNameIdRepository, self)._get_all(stmt)


class SellHistoryAnalyzeResultRepository(AppCurrencyBasedRepository[SellHistoryAnalyzeResult],
                                         ISellHistoryAnalyzeResultRepository):
    def __init__(self, session: AsyncSession):
        super(SellHistoryAnalyzeResultRepository, self).__init__(
            session,
            sell_history_analyze_result_table,
            {
                "timestamp",
                "sells_last_day",
                "sells_last_week",
                "sells_last_month",
                "recommended",
                "deviation",
                "sell_order",
                "sell_order_no_fee",
            }, [
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
            ],
        SellHistoryAnalyzeResult
        )

    async def yield_all(self, app_id: int, currency: int, count: int) -> list[SellHistoryAnalyzeResult]:
        stmt = select(self._select)\
            .where(sell_history_analyze_result_table.c.app_id == app_id)\
            .where(sell_history_analyze_result_table.c.currency == currency)

        async_result = await self._session.stream(stmt)

        while rows := await async_result.fetchmany(count):
            yield [SellHistoryAnalyzeResult(**row) for row in rows]
