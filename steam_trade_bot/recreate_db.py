import asyncio

from dependency_injector.wiring import inject, Provide
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from steam_trade_bot.containers import Container
from steam_trade_bot.infrastructure.models import proxy_metadata, market_metadata
from steam_trade_bot.infrastructure.models.market import currency_table
from steam_trade_bot.settings import BotSettings


@inject
async def main(
    engine=Provide[Container.database.engine]
):
    async with engine.begin() as conn:
        await conn.run_sync(proxy_metadata.drop_all)
        await conn.run_sync(market_metadata.drop_all)
        await conn.run_sync(proxy_metadata.create_all)
        await conn.run_sync(market_metadata.create_all)

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        async with session.begin():
            await session.execute(
                insert(currency_table).values(),
                [
                    {"id": 1, "name": "USD"},
                ],
            )


if __name__ == "__main__":
    print("Are you sure? [y/N]")
    if input() == "y":
        container = Container()
        container.config.from_pydantic(BotSettings())
        container.wire(modules=[__name__])

        asyncio.run(main())
