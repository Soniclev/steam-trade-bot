import asyncio
import functools
import json
from datetime import datetime
from operator import attrgetter, itemgetter

from dependency_injector.wiring import inject, Provide
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.sql.ddl import CreateSchema
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func

from steam_trade_bot.containers import Container
from steam_trade_bot.domain.fee_calculator import compute_fee_from_total, ComputedFee
from steam_trade_bot.domain.services.sell_history_analyzer import steam_date_str_to_datetime
from steam_trade_bot.infrastructure.models.raw_market import market_metadata as raw_market_metadata, \
    market_item_sell_history_table as raw_market_sell_history_table, \
    game_table as raw_game_table, \
    market_item_orders_table as raw_market_item_orders_table

from steam_trade_bot.infrastructure.models.stg_market import market_metadata as stg_market_metadata, \
    game_table as stg_game_table, market_item_stats_table as stg_market_item_stats_table, \
    app_stats_view_name, app_stats_view_select, \
    market_item_sell_history_table as stg_market_item_sell_history_table, \
    market_item_orders_table as stg_market_item_orders_table
from steam_trade_bot.infrastructure.models.dwh_market import market_metadata as dwh_market_metadata
from steam_trade_bot.settings import BotSettings


@functools.lru_cache(typed=False)
def cached_compute_fee_from_total(total: float, game: float | None = None) -> ComputedFee:
    return compute_fee_from_total(total=total, game=game)


def _parse_orders(data: dict) -> tuple[list[tuple], list[tuple]]:
    def _load_from_graph(graph, orders):
        last_quantity = 0
        for price, quantity, _ in graph:
            if price not in orders:
                orders[price] = (price, quantity - last_quantity)
            last_quantity = quantity

    buy_orders = {}
    sell_orders = {}
    _load_from_graph(data["buy_order_graph"], buy_orders)
    _load_from_graph(data["sell_order_graph"], sell_orders)

    return sorted(buy_orders.values(), key=itemgetter(0), reverse=True), sorted(
        sell_orders.values(), key=itemgetter(0), reverse=False
    )


def _extract_sell_history_stats_from_row(row):
    print(row.app_id, row.market_hash_name)
    history = json.loads(row.history)
    points = []
    for item in history:
        timestamp = steam_date_str_to_datetime(item[0])
        price = round(item[1], 2)
        amount = int(item[2])
        points.append((timestamp, price, amount))
    total_sold = sum(x[2] for x in points)
    total_volume = round(sum(x[1] * x[2] for x in points), 2)
    total_volume_steam_fee = round(
        sum(cached_compute_fee_from_total(x[1]).steam * x[2] for x in points),
        2)
    total_volume_publisher_fee = round(
        sum(cached_compute_fee_from_total(x[1]).game * x[2] for x in points),
        2)
    first_sale_timestamp = points[0][0] if points else None
    last_sale_timestamp = points[-1][0] if points else None
    prices = [p[1] for p in points]
    max_price = max(prices) if prices else None
    min_price = min(prices) if prices else None

    return {
        "app_id": row.app_id,
        "market_hash_name": row.market_hash_name,
        "total_sold": total_sold,
        "total_volume": total_volume,
        "total_volume_steam_fee": total_volume_steam_fee,
        "total_volume_publisher_fee": total_volume_publisher_fee,
        "first_sale_timestamp": first_sale_timestamp,
        "last_sale_timestamp": last_sale_timestamp,
        "max_price": max_price,
        "min_price": min_price,
    }


def _extract_sell_history_from_row(row):
    print(row.app_id, row.market_hash_name)
    history = json.loads(row.history)
    points = []
    for item in history:
        timestamp = steam_date_str_to_datetime(item[0]).timestamp()
        price = round(item[1], 2)
        amount = int(item[2])
        points.append((timestamp, price, amount))

    json_history = json.dumps(points)

    return {
        "app_id": row.app_id,
        "market_hash_name": row.market_hash_name,
        "timestamp": row.timestamp,
        "history": json_history,
    }


def _extract_orders_from_row(row):
    print(row.app_id, row.market_hash_name)
    buy_orders, sell_orders = _parse_orders(json.loads(row.dump))

    return {
        "app_id": row.app_id,
        "market_hash_name": row.market_hash_name,
        "timestamp": row.timestamp,
        "buy_orders": json.dumps(buy_orders),
        "sell_orders": json.dumps(sell_orders),
    }


async def _process_sell_history_rows(session, rows):
    stg_market_item_stats_rows = []
    stg_market_item_sell_history = []
    for row in rows:
        stg_market_item_stats_rows.append(_extract_sell_history_stats_from_row(row))
        stg_market_item_sell_history.append(_extract_sell_history_from_row(row))

    if stg_market_item_stats_rows:
        insert_stmt = insert(stg_market_item_stats_table).values()
        await session.execute(
            insert_stmt.on_conflict_do_update(
                        index_elements=['app_id', 'market_hash_name'],
                        set_=dict(
                            total_sold=insert_stmt.excluded.total_sold,
                            total_volume=insert_stmt.excluded.total_volume,
                            total_volume_steam_fee=insert_stmt.excluded.total_volume_steam_fee,
                            total_volume_publisher_fee=insert_stmt.excluded.total_volume_publisher_fee,
                            first_sale_timestamp=insert_stmt.excluded.first_sale_timestamp,
                            last_sale_timestamp=insert_stmt.excluded.last_sale_timestamp,
                            max_price=insert_stmt.excluded.max_price,
                            min_price=insert_stmt.excluded.min_price,
                        )
                    ),
            stg_market_item_stats_rows,
        )

    if stg_market_item_sell_history:
        insert_stmt = insert(stg_market_item_sell_history_table).values()
        await session.execute(
            insert_stmt.on_conflict_do_update(
                index_elements=['app_id', 'market_hash_name'],
                set_=dict(
                    timestamp=insert_stmt.excluded.timestamp,
                    history=insert_stmt.excluded.history,
                )
            ),
            stg_market_item_sell_history,
        )


async def _process_orders_rows(session, rows):
    stg_market_item_orders = []
    for row in rows:
        stg_market_item_orders.append(_extract_orders_from_row(row))

    if stg_market_item_orders:
        insert_stmt = insert(stg_market_item_orders_table).values()
        await session.execute(
            insert_stmt.on_conflict_do_update(
                index_elements=['app_id', 'market_hash_name'],
                set_=dict(
                    timestamp=insert_stmt.excluded.timestamp,
                    buy_orders=insert_stmt.excluded.buy_orders,
                    sell_orders=insert_stmt.excluded.sell_orders,
                )
            ),
            stg_market_item_orders,
        )


@inject
async def main(
        engine=Provide[Container.database.engine]
):
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        async with session.begin():
            await session.execute(delete(stg_market_item_stats_table))
            await _copy_game_from_raw_to_stg(session)
            resp = await session.execute(
                select(raw_market_sell_history_table)
            )
            await _process_sell_history_rows(session, resp)

            resp = await session.execute(
                select(raw_market_item_orders_table)
            )
            await _process_orders_rows(session, resp)


async def _copy_game_from_raw_to_stg(session):
    games = await session.execute(
        select(raw_game_table)
    )
    values = [dict(**x) for x in games.fetchall()]
    if values:
        insert_stmt = insert(stg_game_table).values()
        await session.execute(
            insert_stmt.on_conflict_do_update(
                index_elements=['app_id'],
                set_=dict(
                    name=insert_stmt.excluded.name,
                    icon_url=insert_stmt.excluded.icon_url,
                    is_publisher_valve=insert_stmt.excluded.is_publisher_valve,
                )
            ),
            values,
        )


if __name__ == "__main__":
    container = Container()
    container.config.from_pydantic(BotSettings())
    container.wire(modules=[__name__])

    asyncio.run(main())
