import operator
from dataclasses import asdict
from operator import attrgetter
from typing import TypeVar, Generic, Literal

from steam_trade_bot.domain.exceptions import SerializationError
from sqlalchemy import delete, select, Table, or_
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
    MarketItemOrders, MarketItemSellHistoryStats, EntireMarketDailyStats,
)
from steam_trade_bot.domain.interfaces.repositories import (
    IGameRepository,
    IMarketItemRepository,
    IMarketItemSellHistoryRepository,
    ISellHistoryAnalyzeResultRepository,
    IMarketItemInfoRepository,
    IMarketItemNameIdRepository,
    IMarketItemOrdersRepository, IMarketItemSellHistoryStatsRepository,
    IEntireMarketDailyStatsRepository,
)
from steam_trade_bot.infrastructure.models.market import (
    sell_history_analyze_result_table,
    market_item_info_table,
    market_item_name_id_table,
)
from steam_trade_bot.infrastructure.models.dwh_market import (
    game_table,
    market_item_table,
    market_item_sell_history_table,
    market_item_stats_table,
    market_item_orders_table,
    entire_market_stats_table,
)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    def __init__(self,
                 session: AsyncSession,
                 table: Table,
                 type_: type,
                 conflict_index: set[str],
                 on_conflict_update: set[str] | None = None,
                 ):
        self._session = session
        self._table = table
        self._conflict_index_set = conflict_index
        self._all_columns = [c.name for c in table.c]
        if not on_conflict_update:
            on_conflict_update = set(self._all_columns) - set(self._conflict_index_set)
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


class AppMarketNameBasedRepository(BaseRepository[T]):
    def __init__(self, session: AsyncSession, table: Table, type_: type):
        super().__init__(session, table, type_, {"app_id", "market_hash_name"})
        self._select = [
            attrgetter(column)(table.c)
            for column in self._all_columns
        ]

    async def remove(self, app_id: int, market_hash_name: str):
        await super(AppMarketNameBasedRepository, self)._remove(
            delete(self._table)
            .where(self._table.c.app_id == app_id)
            .where(self._table.c.market_hash_name == market_hash_name)
        )

    async def get(
            self, app_id: int, market_hash_name: str
    ) -> T | None:
        return await super(AppMarketNameBasedRepository, self)._get(
            select(self._select)
            .where(self._table.c.app_id == app_id)
            .where(self._table.c.market_hash_name == market_hash_name)
        )

    async def get_all(
            self, app_id: int, offset: int = None, count: int = None
    ) -> list[T]:
        stmt = select(self._select) \
            .where(self._table.c.app_id == app_id)
        if count:
            stmt = stmt.limit(count)
        if offset:
            stmt = stmt.offset(offset)
        return await super(AppMarketNameBasedRepository, self)._get_all(stmt)

    async def yield_all_by_pairs(self, pairs: list[tuple[int, str]], count: int) -> list[T]:
        filter_conditions = []
        for app_id, market_hash_name in pairs:
            filter_conditions.append(
                (self._table.c.app_id == app_id) &
                (self._table.c.market_hash_name == market_hash_name)
            )

        stmt = select(self._select).where(or_(*filter_conditions))

        async_result = await self._session.stream(stmt)

        while rows := await async_result.fetchmany(count):
            yield [self._type(**row) for row in rows]

    async def yield_all(self, app_id: int, count: int) -> list[T]:
        stmt = select(self._select) \
            .where(self._table.c.app_id == app_id)

        async_result = await self._session.stream(stmt)

        while rows := await async_result.fetchmany(count):
            yield [self._type(**row) for row in rows]


class GameRepository(BaseRepository[Game], IGameRepository):
    def __init__(self, session: AsyncSession, table=game_table, type_=Game):
        super().__init__(session, table, type_, {"app_id"})

    async def remove(self, app_id: int):
        await super(GameRepository).remove(
            delete(self._table).where(self._table.c.app_id == app_id)
        )

    async def get(self, app_id: int) -> Game | None:
        return await super(GameRepository).get(
            select(self._table).where(self._table.c.app_id == app_id)
        )

    async def yield_all_by_app_ids(self, app_ids: list[int], count: int) -> list[T]:
        filter_conditions = []
        for app_id in app_ids:
            filter_conditions.append(
                (self._table.c.app_id == app_id)
            )

        stmt = select(self._table).where(or_(*filter_conditions))

        async_result = await self._session.stream(stmt)

        while rows := await async_result.fetchmany(count):
            yield [self._type(**row) for row in rows]

    async def get_all(self, offset: int = None, count: int = None) -> list[Game]:
        stmt = select(self._table)
        if offset:
            stmt = stmt.offset(offset)
        if count:
            stmt = stmt.limit(count)
        return await super(GameRepository, self)._get_all(stmt)


class MarketItemInfoRepository(AppMarketNameBasedRepository[MarketItemInfo],
                               IMarketItemInfoRepository):
    def __init__(self, session: AsyncSession):
        super(MarketItemInfoRepository, self).__init__(
            session, market_item_info_table, MarketItemInfo
        )


class MarketItemRepository(AppMarketNameBasedRepository[MarketItem], IMarketItemRepository):
    def __init__(self, session: AsyncSession):
        super(MarketItemRepository, self).__init__(
            session, market_item_table, MarketItem
        )


class MarketItemOrdersRepository(AppMarketNameBasedRepository[MarketItemOrders],
                                 IMarketItemOrdersRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        super(MarketItemOrdersRepository, self).__init__(
            session, market_item_orders_table, MarketItemOrders
        )


class MarketItemSellHistoryRepository(AppMarketNameBasedRepository[MarketItemSellHistory],
                                      IMarketItemSellHistoryRepository):
    def __init__(self, session: AsyncSession):
        super(MarketItemSellHistoryRepository, self).__init__(
            session, market_item_sell_history_table, MarketItemSellHistory
        )


class MarketItemSellHistoryStatsRepository(AppMarketNameBasedRepository[MarketItemSellHistoryStats],
                                           IMarketItemSellHistoryStatsRepository):
    def __init__(self, session: AsyncSession):
        super(MarketItemSellHistoryStatsRepository, self).__init__(
            session, market_item_stats_table, MarketItemSellHistoryStats
        )


class MarketItemNameIdRepository(AppMarketNameBasedRepository[MarketItemNameId], IMarketItemNameIdRepository):
    def __init__(self, session: AsyncSession):
        super(MarketItemNameIdRepository, self).__init__(
            session, market_item_name_id_table, MarketItemNameId
        )


class SellHistoryAnalyzeResultRepository(AppMarketNameBasedRepository[SellHistoryAnalyzeResult],
                                         ISellHistoryAnalyzeResultRepository):
    def __init__(self, session: AsyncSession):
        super(SellHistoryAnalyzeResultRepository, self).__init__(
            session, sell_history_analyze_result_table, SellHistoryAnalyzeResult
        )


class EntireMarketDailyStatsRepository(BaseRepository[EntireMarketDailyStats], IEntireMarketDailyStatsRepository):
    def __init__(self, session: AsyncSession, table=entire_market_stats_table, type_=EntireMarketDailyStats):
        super().__init__(session, table, type_, {"point_timestamp"})

    async def remove(self, point_timestamp: int):
        await super(EntireMarketDailyStatsRepository).remove(
            delete(self._table).where(self._table.c.point_timestamp == point_timestamp)
        )

    async def get(self, point_timestamp: int) -> EntireMarketDailyStats | None:
        return await super(EntireMarketDailyStatsRepository).get(
            select(self._table).where(self._table.c.point_timestamp == point_timestamp)
        )

    async def yield_all_by_app_ids(self, point_timestamps: list[int], count: int) -> list[T]:
        filter_conditions = []
        for point_timestamp in point_timestamps:
            filter_conditions.append(
                (self._table.c.point_timestamp == point_timestamp)
            )

        stmt = select(self._table).where(or_(*filter_conditions))

        async_result = await self._session.stream(stmt)

        while rows := await async_result.fetchmany(count):
            yield [self._type(**row) for row in rows]

    async def get_all(self, mode: Literal["monthly", "weekly", "daily"] = "daily", offset: int = None, count: int = None) -> list[EntireMarketDailyStats]:
        stmt = select(self._table).where(self._table.c.mode == mode).order_by(self._table.c.point_timestamp.asc())
        if offset:
            stmt = stmt.offset(offset)
        if count:
            stmt = stmt.limit(count)
        return await super(EntireMarketDailyStatsRepository, self)._get_all(stmt)
