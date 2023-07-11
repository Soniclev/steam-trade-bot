import asyncio

from dependency_injector.wiring import inject, Provide
from sqlalchemy.sql import text
from sqlalchemy.sql.ddl import CreateSchema

from steam_trade_bot.containers import Container
from steam_trade_bot.infrastructure.models.raw_market import market_metadata as raw_market_metadata
from steam_trade_bot.infrastructure.models.stg_market import market_metadata as stg_market_metadata, app_stats_view_name as stg_app_stats_view_name , app_stats_view_select as stg_app_stats_view_select
from steam_trade_bot.infrastructure.models.dwh_market import market_metadata as dwh_market_metadata, app_stats_view_name as dwh_app_stats_view_name, app_stats_view_select as dwh_app_stats_view_select
from steam_trade_bot.infrastructure.models.raw_market import SCHEMA_NAME as RAW_SCHEMA_NAME
from steam_trade_bot.infrastructure.models.stg_market import SCHEMA_NAME as STG_SCHEMA_NAME
from steam_trade_bot.infrastructure.models.dwh_market import SCHEMA_NAME as DWH_SCHEMA_NAME
from steam_trade_bot.settings import BotSettings


async def recreate_raw(engine):
    async with engine.begin() as conn:
        await _create_schema_if_not_exists(conn, engine, RAW_SCHEMA_NAME)
        await conn.run_sync(raw_market_metadata.drop_all)
        await conn.run_sync(raw_market_metadata.create_all)
        with open("etc/copy_to_raw.sql", 'r') as f:
            sql_statements = f.read().split(';\n')  # Split SQL statements by semicolon
            for statement in sql_statements:
                statement = statement.strip()
                if statement:  # Skip empty statements
                    await conn.execute(text(statement))


async def recreate_stg_dwh(engine):
    async with engine.begin() as conn:
        await _create_schema_if_not_exists(conn, engine, STG_SCHEMA_NAME)
        await _create_schema_if_not_exists(conn, engine, DWH_SCHEMA_NAME)
        await conn.execute(text(f"DROP VIEW IF EXISTS {STG_SCHEMA_NAME}.{stg_app_stats_view_name}"))
        await conn.execute(text(f"DROP VIEW IF EXISTS {DWH_SCHEMA_NAME}.{dwh_app_stats_view_name}"))
        await conn.run_sync(stg_market_metadata.drop_all)
        await conn.run_sync(dwh_market_metadata.drop_all)
        await conn.run_sync(stg_market_metadata.create_all)
        await conn.run_sync(dwh_market_metadata.create_all)
        await conn.execute(text(f"CREATE VIEW {STG_SCHEMA_NAME}.{stg_app_stats_view_name} AS " + stg_app_stats_view_select))
        await conn.execute(text(f"CREATE VIEW {DWH_SCHEMA_NAME}.{dwh_app_stats_view_name} AS " + dwh_app_stats_view_select))


@inject
async def main(
    engine=Provide[Container.database.engine]
):
    pass
    # await recreate_raw(engine)
    await recreate_stg_dwh(engine)


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
