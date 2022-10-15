import asyncio
from typing import Callable

from dependency_injector.wiring import Provide, inject
from sqlalchemy import insert
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from steam_trade_bot.containers import Container
from steam_trade_bot.domain.entities.market import Game, MarketItem
from steam_trade_bot.domain.services.market_item_importer import MarketItemImporter
from steam_trade_bot.domain.services.sell_history_analyzer import SellHistoryAnalyzer
from steam_trade_bot.infrastructure.models.market import game_table
from steam_trade_bot.infrastructure.repositories import GameRepository, MarketItemRepository
from steam_trade_bot.settings import BotSettings


@inject
async def main(

        market_item_importer: MarketItemImporter = Provide[Container.services.market_item_importer],
        sell_history_analyzer: SellHistoryAnalyzer = Provide[
            Container.services.sell_history_analyzer],
) -> None:
    await sell_history_analyzer.analyze(app_id=730,
                                        market_hash_name="Stockholm 2021 Mirage Souvenir Package",
                                        expected_profit=0.05)

    # await market_item_importer.import_item(app_id=730, market_hash_name="Prisma 2 Case")
    # await market_item_importer.import_item(app_id=730, market_hash_name="Stockholm 2021 Mirage Souvenir Package")


if __name__ == "__main__":
    container = Container()
    container.config.from_pydantic(BotSettings())
    container.wire(modules=[__name__])

    asyncio.run(main())
