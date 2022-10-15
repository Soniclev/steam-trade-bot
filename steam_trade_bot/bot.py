import asyncio
from typing import Callable

from dependency_injector.wiring import Provide, inject
from sqlalchemy import insert
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from steam_trade_bot.containers import Container
from steam_trade_bot.domain.entities.market import Game, MarketItem
from steam_trade_bot.infrastructure.models.market import game_table
from steam_trade_bot.infrastructure.repositories import GameRepository, MarketItemRepository
from steam_trade_bot.settings import BotSettings


@inject
async def main(
    game_rep: GameRepository = Provide[Container.repositories.game],
    item_rep: MarketItemRepository = Provide[Container.repositories.market_item],
) -> None:
    await game_rep.remove(app_id=570)
    await game_rep.add(Game(app_id=570, name="Dota 2", publisher_fee=0.1))
    print(await game_rep.get(app_id=570))

    await item_rep.remove(app_id=570, market_hash_name="Recoil Case")
    await item_rep.add(
        MarketItem(
            app_id=730, market_hash_name="Recoil Case", commodity=True, item_name_id=176321160
        )
    )
    print(await item_rep.get(app_id=730, market_hash_name="Recoil Case"))


if __name__ == "__main__":
    container = Container()
    container.config.from_pydantic(BotSettings())
    container.wire(modules=[__name__])

    asyncio.run(main())
