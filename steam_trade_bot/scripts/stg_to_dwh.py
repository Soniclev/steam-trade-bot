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
from steam_trade_bot.infrastructure.models.dwh_market import market_metadata as dwh_market_metadata, \
    market_item_sell_history_table as dwh_market_item_sell_history_table, \
    game_table as dwh_game_table, \
    market_item_stats_table as dwh_market_item_stats_table, \
    market_item_orders_table as dwh_market_item_orders_table

from steam_trade_bot.infrastructure.models.stg_market import market_metadata as stg_market_metadata, \
    game_table as stg_game_table, market_item_stats_table as stg_market_item_stats_table, \
    app_stats_view_name, app_stats_view_select, \
    market_item_sell_history_table as stg_market_item_sell_history_table, \
    market_item_orders_table as stg_market_item_orders_table
from steam_trade_bot.infrastructure.models.dwh_market import market_metadata as dwh_market_metadata
from steam_trade_bot.settings import BotSettings


def _extract_sell_history_stats_from_row(row):
    print(row.app_id, row.market_hash_name)

    return {
        "app_id": row.app_id,
        "market_hash_name": row.market_hash_name,
        "total_sold": row.total_sold,
        "total_volume": row.total_volume,
        "total_volume_steam_fee": row.total_volume_steam_fee,
        "total_volume_publisher_fee": row.total_volume_publisher_fee,
        "first_sale_timestamp": row.first_sale_timestamp,
        "last_sale_timestamp": row.last_sale_timestamp,
        "max_price": row.max_price,
        "min_price": row.min_price,
    }


def _extract_sell_history_from_row(row):
    print(row.app_id, row.market_hash_name)

    return {
        "app_id": row.app_id,
        "market_hash_name": row.market_hash_name,
        "timestamp": row.timestamp,
        "history": row.history,
    }


def _extract_orders_from_row(row):
    print(row.app_id, row.market_hash_name)

    return {
        "app_id": row.app_id,
        "market_hash_name": row.market_hash_name,
        "timestamp": row.timestamp,
        "buy_orders": row.buy_orders,
        "sell_orders": row.sell_orders,
    }


async def _process_sell_history_rows(session, rows):
    stg_market_item_sell_history = []
    for row in rows:
        stg_market_item_sell_history.append(_extract_sell_history_from_row(row))

    insert_stmt = insert(dwh_market_item_sell_history_table).values()
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


async def _process_stats_rows(session, rows):
    stg_market_item_stats_rows = []
    for row in rows:
        stg_market_item_stats_rows.append(_extract_sell_history_stats_from_row(row))

    insert_stmt = insert(dwh_market_item_stats_table).values()
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


async def _process_orders_rows(session, rows):
    stg_market_item_orders = []
    for row in rows:
        stg_market_item_orders.append(_extract_orders_from_row(row))

    insert_stmt = insert(dwh_market_item_orders_table).values()
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
            await session.execute(delete(dwh_market_item_stats_table))
            await _copy_game_from_raw_to_stg(session)
            resp = await session.execute(
                select(stg_market_item_sell_history_table)
            )
            await _process_sell_history_rows(session, resp)

            resp = await session.execute(
                select(stg_market_item_stats_table)
            )
            await _process_stats_rows(session, resp)

            resp = await session.execute(
                select(stg_market_item_orders_table)
            )
            await _process_orders_rows(session, resp)


async def _copy_game_from_raw_to_stg(session):
    games = await session.execute(
        select(stg_game_table)
    )
    insert_stmt = insert(dwh_game_table).values()
    await session.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=['app_id'],
            set_=dict(
                name=insert_stmt.excluded.name,
                icon_url=insert_stmt.excluded.icon_url,
                is_publisher_valve=insert_stmt.excluded.is_publisher_valve,
            )
        ),
        [dict(**x) for x in games.fetchall()],
    )


if __name__ == "__main__":
    container = Container()
    container.config.from_pydantic(BotSettings())
    container.wire(modules=[__name__])

    asyncio.run(main())
