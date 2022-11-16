import asyncio
from pathlib import Path
from typing import Callable

from dependency_injector.wiring import Provide, inject
from sqlalchemy import insert
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from steam_trade_bot.consts import DEFAULT_CURRENCY
from steam_trade_bot.containers import Container
from steam_trade_bot.domain.entities.market import Game, MarketItem
from steam_trade_bot.domain.services.market_item_importer import (
    MarketItemImporterFromSearch,
    MarketItemImporterFromPage,
    MarketItemImporterFromOrdersHistogram,
)
from steam_trade_bot.domain.services.sell_history_analyzer import SellHistoryAnalyzer
from steam_trade_bot.domain.services.ste_export import STEExport
from steam_trade_bot.infrastructure.models.market import game_table
from steam_trade_bot.infrastructure.repositories import GameRepository, MarketItemRepository
from steam_trade_bot.settings import BotSettings


@inject
async def main(
    market_item_importer_from_search: MarketItemImporterFromSearch = Provide[
        Container.services.market_item_importer_from_search
    ],
    market_item_importer_from_page: MarketItemImporterFromPage = Provide[
        Container.services.market_item_importer_from_page
    ],
    market_item_importer_from_orders: MarketItemImporterFromOrdersHistogram = Provide[
        Container.services.market_item_importer_from_orders
    ],
    sell_history_analyzer: SellHistoryAnalyzer = Provide[Container.services.sell_history_analyzer],
    ste_export: STEExport = Provide[Container.services.ste_export],
) -> None:
    pass
    # path = Path(
    #     r"C:\Users\User\AppData\Local\Google\Chrome\User Data\Default\databases\chrome-extension_bkhnfcfghceoifdblnpcjhlmeibdmlaj_0\3"
    # )
    # await ste_export.export(path)
    # await sell_history_analyzer.analyze(app_id=730,
    #                                     market_hash_name="Stockholm 2021 Mirage Souvenir Package",
    #                                     currency=1)

    # await market_item_importer.import_items_from_url(
    #     "https://steamcommunity.com/market/search/render/?query=&start=0&count=100&appid=730&search_descriptions=0&sort_column=name&sort_dir=desc&norender=1",
    # )

    # await market_item_importer_from_search.import_items_from_url(
    #     "https://steamcommunity.com/market/search/render/?query=&start=0&count=100&search_descriptions=0&sort_column=quantity&sort_dir=asc",
    #     currency=DEFAULT_CURRENCY
    # )

    await market_item_importer_from_page.import_from_all_games(currency=DEFAULT_CURRENCY)
    # await market_item_importer_from_page.import_from_db(app_id=730, currency=DEFAULT_CURRENCY)
    # await market_item_importer_from_page.import_item(app_id=440, market_hash_name="Mann Co. Supply Munition Series #91" ,currency=DEFAULT_CURRENCY)
    await market_item_importer_from_orders.import_orders_from_all_games(currency=DEFAULT_CURRENCY)
    # await market_item_importer_from_orders.import_orders_from_db(app_id=753, currency=1)
    # await market_item_importer.import_item_orders(app_id=730, market_hash_name="Danger Zone Case")

    # await market_item_importer.import_from_all_games(currency=1)

    # await market_item_importer_from_page.import_from_db(app_id=730, currency=DEFAULT_CURRENCY)

    # await market_item_importer_from_page.import_item(
    #     app_id=730, market_hash_name="Prisma 2 Case", currency=1
    # )

    # await market_item_importer.import_item(app_id=730, market_hash_name="Prisma 2 Case")
    # await market_item_importer.import_item(app_id=730, market_hash_name="Stockholm 2021 Mirage Souvenir Package")
    # await market_item_importer.import_item(app_id=730, market_hash_name="★ Gut Knife | Bright Water (Factory New)")
    # await market_item_importer.import_item(app_id=730, market_hash_name="★ Huntsman Knife | Ultraviolet (Field-Tested)")
    # await market_item_importer.import_item(app_id=730, market_hash_name="Danger Zone Case")
    # await market_item_importer.import_item(app_id=730, market_hash_name="Clutch Case")


if __name__ == "__main__":
    container = Container()
    container.config.from_pydantic(BotSettings())
    container.wire(modules=[__name__])

    asyncio.run(main())
