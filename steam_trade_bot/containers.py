# pylint: disable=E1101
from typing import Callable

import aioredis
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from steam_trade_bot.domain.services.export_yaml import ExportYaml
from steam_trade_bot.domain.services.market_item_importer import (
    MarketItemImporterFromSearch,
    MarketItemImporterFromOrdersHistogram,
    MarketItemImporterFromPage,
)
from steam_trade_bot.domain.services.sell_history_analyzer import SellHistoryAnalyzer
from steam_trade_bot.domain.services.ste_export import STEExport
from steam_trade_bot.infrastructure.proxy import ProxyRepository, ProxyProvider
from steam_trade_bot.infrastructure.session import SteamSessionProvider

from steam_trade_bot.infrastructure.unit_of_work import UnitOfWork


class Database(containers.DeclarativeContainer):
    config = providers.Configuration()

    engine = providers.Singleton(  # type: ignore
        create_async_engine,
        config.database,
        isolation_level="REPEATABLE READ",
    )

    session_factory: Callable[..., AsyncSession] = providers.Factory(
        sessionmaker, engine, expire_on_commit=False, class_=AsyncSession
    )

    redis = providers.Singleton(
        aioredis.from_url,
        config.redis,
    )


class Repositories(containers.DeclarativeContainer):
    config = providers.Configuration()
    database = providers.DependenciesContainer()

    proxy = providers.Singleton(
        ProxyRepository,
        database.session_factory,
    )

    unit_of_work = providers.Factory(
        UnitOfWork,
        database.session_factory,
    )


class Infrastructure(containers.DeclarativeContainer):
    config = providers.Configuration()
    repositories = providers.DependenciesContainer()
    database = providers.DependenciesContainer()

    proxy_provider = providers.Singleton(
        ProxyProvider,
        repositories.proxy,
        database.redis,
    )

    steam_session_provider = providers.Singleton(
        SteamSessionProvider,
        proxy_provider,
        database.redis,
    )


class Services(containers.DeclarativeContainer):
    config = providers.Configuration()
    infrastructure = providers.DependenciesContainer()
    repositories = providers.DependenciesContainer()

    sell_history_analyzer = providers.Singleton(
        SellHistoryAnalyzer,
    )

    market_item_importer_from_search = providers.Singleton(
        MarketItemImporterFromSearch,
        repositories.unit_of_work.provider,
        infrastructure.steam_session_provider,
        config.market_item_search,
    )

    market_item_importer_from_page = providers.Singleton(
        MarketItemImporterFromPage,
        repositories.unit_of_work.provider,
        sell_history_analyzer,
        infrastructure.steam_session_provider,
        config.market_item_page,
    )

    market_item_importer_from_orders = providers.Singleton(
        MarketItemImporterFromOrdersHistogram,
        repositories.unit_of_work.provider,
        infrastructure.steam_session_provider,
        config.market_item_orders,
    )

    ste_export = providers.Singleton(
        STEExport,
        repositories.unit_of_work.provider,
    )

    export_yaml = providers.Singleton(
        ExportYaml,
        repositories.unit_of_work.provider,
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

    infrastructure = providers.Container(
        Infrastructure,
        database=database,
        repositories=repositories,
    )

    services = providers.Container(
        Services, config=config, repositories=repositories, infrastructure=infrastructure
    )
