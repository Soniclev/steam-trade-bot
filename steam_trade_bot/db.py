import asyncio

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from steam_trade_bot.infrastructure.models.market import metadata, game_table, currency_table


async def main():
    engine = create_async_engine(
        "postgresql+asyncpg://gaben:qwerty@localhost/trade_bot", isolation_level="REPEATABLE READ"
    )

    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                insert(game_table).values(),
                [
                    {"app_id": 730, "name": "CS:GO"},
                ],
            )
            result = await session.execute(
                insert(currency_table).values(),
                [
                    {"id": 1, "name": "USD"},
                ],
            )


if __name__ == "__main__":
    asyncio.run(main())
