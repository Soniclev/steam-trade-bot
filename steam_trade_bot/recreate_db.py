import asyncio

from dependency_injector.wiring import inject, Provide
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.sql.ddl import CreateSchema

from steam_trade_bot.containers import Container
from steam_trade_bot.infrastructure.models.raw_market import market_metadata as raw_market_metadata
from steam_trade_bot.infrastructure.models.stg_market import market_metadata as stg_market_metadata, game_table as stg_game_table, market_item_stats_table as stg_market_item_stats_table, app_stats_view_name, app_stats_view_select
from steam_trade_bot.infrastructure.models.dwh_market import market_metadata as dwh_market_metadata
from steam_trade_bot.infrastructure.models import proxy_metadata
from steam_trade_bot.infrastructure.models.raw_market import SCHEMA_NAME as RAW_SCHEMA_NAME
from steam_trade_bot.infrastructure.models.stg_market import SCHEMA_NAME as STG_SCHEMA_NAME
from steam_trade_bot.infrastructure.models.dwh_market import SCHEMA_NAME as DWH_SCHEMA_NAME
from steam_trade_bot.settings import BotSettings


@inject
async def main(
    engine=Provide[Container.database.engine]
):
    async with engine.begin() as conn:
        # await _create_schema_if_not_exists(conn, engine, RAW_SCHEMA_NAME)
        # await _create_schema_if_not_exists(conn, engine, STG_SCHEMA_NAME)
        await _create_schema_if_not_exists(conn, engine, DWH_SCHEMA_NAME)
        await conn.execute(text(f"DROP VIEW IF EXISTS {STG_SCHEMA_NAME}.{app_stats_view_name}"))
        # await conn.run_sync(proxy_metadata.drop_all)
        # await conn.run_sync(raw_market_metadata.drop_all)
        # await conn.run_sync(stg_market_metadata.drop_all)
        await conn.run_sync(dwh_market_metadata.drop_all)
        # await conn.run_sync(proxy_metadata.create_all)
        # await conn.run_sync(raw_market_metadata.create_all)
        # await conn.run_sync(stg_market_metadata.create_all)
        await conn.run_sync(dwh_market_metadata.create_all)
        await conn.execute(text(f"CREATE VIEW {STG_SCHEMA_NAME}.{app_stats_view_name} AS " + app_stats_view_select))

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:

        async with session.begin():
            pass
            # await session.execute(
            #     insert(stg_game_table).values(),
            #     [
            #         {"app_id": 730, "name": "CSGO"},
            #     ],
            # )
            # await session.execute(
            #     insert(stg_market_item_stats_table).values(),
            #     [
            #         {"app_id": 730, "market_hash_name": "CSGO", "total_sold": 123, "total_volume": 456, "total_volume_steam_fee": 34, "total_volume_publisher_fee": 54},
            #     ],
            # )


async def _create_schema_if_not_exists(conn, engine, schema_name: str):
    has_schema = await conn.run_sync(engine.dialect.has_schema, schema_name)
    if not has_schema:
        raw_schema = CreateSchema(schema_name)
        await conn.execute(raw_schema)


if __name__ == "__main__":
    print("Are you sure? [y/N]")
    if input() == "y":
        container = Container()
        container.config.from_pydantic(BotSettings())
        container.wire(modules=[__name__])

        asyncio.run(main())
