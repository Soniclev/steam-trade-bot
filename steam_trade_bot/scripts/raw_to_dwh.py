import asyncio
from operator import attrgetter

from dependency_injector.wiring import inject, Provide
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

from steam_trade_bot.containers import Container
from steam_trade_bot.etl.models import MarketItemRaw, MarketItemSellHistoryRaw, MarketItemOrdersRaw, \
    GameRaw
from steam_trade_bot.etl.processors.game import process_game
from steam_trade_bot.etl.processors.market_item import process_market_item, \
    process_market_item_sell_history, process_market_item_orders
from steam_trade_bot.infrastructure.models.raw_market import market_item_table as raw_market_item_table, \
    market_item_sell_history_table as raw_market_sell_history_table, \
    game_table as raw_game_table, \
    market_item_orders_table as raw_market_item_orders_table

from steam_trade_bot.infrastructure.models.stg_market import market_item_table as stg_market_item_table, \
    game_table as stg_game_table, market_item_stats_table as stg_market_item_stats_table, \
    market_item_sell_history_table as stg_market_item_sell_history_table, \
    market_item_orders_table as stg_market_item_orders_table

from steam_trade_bot.infrastructure.models.dwh_market import market_item_table as dwh_market_item_table, \
    market_item_sell_history_table as dwh_market_item_sell_history_table, \
    market_item_stats_table as dwh_market_item_stats_table, \
    market_item_orders_table as dwh_market_item_orders_table, \
    game_table as dwh_game_table

from steam_trade_bot.settings import BotSettings


async def _upsert_many(session, table, values, index_elements: list[str], set_: list[str]):
    if values:
        insert_stmt = insert(table).values()
        set_ = {
            column: attrgetter(column)(insert_stmt.excluded)
            for column in set_
        }
        await session.execute(
            insert_stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=set_
            ),
            values,
        )


async def _peek_items_to_process(session, count) -> list[tuple[int, str]]:
    rows = await session.execute(
        select(raw_market_item_table).limit(count)
    )
    return [
        (row.app_id, row.market_hash_name) for row in rows
    ]


@inject
async def main(
        engine=Provide[Container.database.engine]
):
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        async with session.begin():
            await session.execute(delete(stg_market_item_sell_history_table))
            await session.execute(delete(dwh_market_item_sell_history_table))
            await session.execute(delete(stg_market_item_stats_table))
            await session.execute(delete(dwh_market_item_stats_table))
            await session.execute(delete(stg_market_item_orders_table))
            await session.execute(delete(dwh_market_item_orders_table))
            await _process_game_raw_stg_dwh(session)
            items_keys = await _peek_items_to_process(session, 10)
            await _process_items_raw_stage_dwh(session, items_keys)
            await _process_sell_history_raw_stage_dwh(session, items_keys)
            await _process_orders_raw_stage_dwh(session, items_keys)


async def _process_items_raw_stage_dwh(session, items_keys):
    filter_conditions = []
    for app_id, market_hash_name in items_keys:
        filter_conditions.append(
            (raw_market_item_table.c.app_id == app_id) &
            (raw_market_item_table.c.market_hash_name == market_hash_name)
        )

    resp = await session.execute(
        select(raw_market_item_table).where(or_(*filter_conditions))
    )
    stage_list = []
    dwh_list = []
    for row in resp:
        stage, dwh = process_market_item(MarketItemRaw(**row))
        stage_list.append(stage)
        dwh_list.append(dwh)

    await _upsert_many(session, stg_market_item_table, stage_list,
                       ["app_id", "market_hash_name"],
                       ["market_fee", "market_marketable_restriction", "market_tradable_restriction", "commodity", "icon_url"])
    await _upsert_many(session, dwh_market_item_table, dwh_list,
                       ["app_id", "market_hash_name"],
                       ["market_fee", "market_marketable_restriction", "market_tradable_restriction", "commodity", "icon_url"])


async def _process_sell_history_raw_stage_dwh(session, items_keys):
    filter_conditions = []
    for app_id, market_hash_name in items_keys:
        filter_conditions.append(
            (raw_market_sell_history_table.c.app_id == app_id) &
            (raw_market_sell_history_table.c.market_hash_name == market_hash_name)
        )

    resp = await session.execute(
        select(raw_market_sell_history_table).where(or_(*filter_conditions))
    )
    sell_history_stage_list = []
    sell_history_dwh_list = []
    stats_stage_list = []
    stats_dwh_list = []
    for row in resp:
        sell_history_stage, \
            sell_history_dwh, \
            stats_stage, \
            stats_dwh = process_market_item_sell_history(MarketItemSellHistoryRaw(**row))
        sell_history_stage_list.append(sell_history_stage)
        sell_history_dwh_list.append(sell_history_dwh)
        stats_stage_list.append(stats_stage)
        stats_dwh_list.append(stats_dwh)
    await _upsert_many(session, stg_market_item_sell_history_table, sell_history_stage_list,
                       ["app_id", "market_hash_name"],
                       ["timestamp", "history"])
    await _upsert_many(session, dwh_market_item_sell_history_table, sell_history_dwh_list,
                       ["app_id", "market_hash_name"],
                       ["timestamp", "history"])
    await _upsert_many(session, stg_market_item_stats_table, stats_stage_list,
                       ["app_id", "market_hash_name"],
                       ["total_sold", "total_volume", "total_volume_steam_fee",
                        "total_volume_publisher_fee", "min_price", "max_price",
                        "first_sale_timestamp", "last_sale_timestamp"])
    await _upsert_many(session, dwh_market_item_stats_table, stats_dwh_list,
                       ["app_id", "market_hash_name"],
                       ["total_sold", "total_volume", "total_volume_steam_fee",
                        "total_volume_publisher_fee", "min_price", "max_price",
                        "first_sale_timestamp", "last_sale_timestamp"])


async def _process_orders_raw_stage_dwh(session, items_keys):
    filter_conditions = []
    for app_id, market_hash_name in items_keys:
        filter_conditions.append(
            (raw_market_item_orders_table.c.app_id == app_id) &
            (raw_market_item_orders_table.c.market_hash_name == market_hash_name)
        )

    resp = await session.execute(
        select(raw_market_item_orders_table).where(or_(*filter_conditions))
    )
    stage_list = []
    dwh_list = []
    for row in resp:
        stage, dwh = process_market_item_orders(MarketItemOrdersRaw(**row))
        stage_list.append(stage)
        dwh_list.append(dwh)

    await _upsert_many(session, stg_market_item_orders_table, stage_list,
                       ["app_id", "market_hash_name"],
                       ["timestamp", "buy_orders", "sell_orders"])
    await _upsert_many(session, dwh_market_item_orders_table, dwh_list,
                       ["app_id", "market_hash_name"],
                       ["timestamp", "buy_orders", "sell_orders"])


async def _process_game_raw_stg_dwh(session):
    games = await session.execute(
        select(raw_game_table)
    )
    stage_list = []
    dwh_list = []
    for row in games:
        stage, dwh = process_game(GameRaw(**row))
        stage_list.append(stage)
        dwh_list.append(dwh)
    await _upsert_many(session, stg_game_table, stage_list,
                       ["app_id"],
                       ["name", "icon_url", "is_publisher_valve"])
    await _upsert_many(session, dwh_game_table, dwh_list,
                       ["app_id"],
                       ["name", "icon_url", "is_publisher_valve"])


if __name__ == "__main__":
    container = Container()
    container.config.from_pydantic(BotSettings())
    container.wire(modules=[__name__])

    asyncio.run(main())
