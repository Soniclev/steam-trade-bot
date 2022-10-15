from typing import Callable

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from steam_trade_bot.infrastructure.repositories import GameRepository, MarketItemRepository


class Database(containers.DeclarativeContainer):
    config = providers.Configuration()

    engine = providers.Singleton(  # type: ignore
        create_async_engine,
        config.database,
        isolation_level="REPEATABLE READ",
    )

    session: Callable[..., AsyncSession] = providers.Factory(
        sessionmaker, engine, expire_on_commit=False, class_=AsyncSession
    )


class Repositories(containers.DeclarativeContainer):
    config = providers.Configuration()
    database = providers.DependenciesContainer()

    game = providers.Singleton(
        GameRepository,
        database.session,
    )

    market_item = providers.Singleton(
        MarketItemRepository,
        database.session,
    )


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    database = providers.Container(
        Database,
        config=config,
    )
    repositories = providers.Container(
        Repositories,
        database=database,
    )
