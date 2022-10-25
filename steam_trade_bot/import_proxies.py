import asyncio
from pathlib import Path
from typing import Callable

from dependency_injector.wiring import Provide, inject
from sqlalchemy import insert
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from steam_trade_bot.containers import Container
from steam_trade_bot.domain.entities.market import Game, MarketItem
from steam_trade_bot.domain.entities.proxy import Proxy
from steam_trade_bot.domain.services.market_item_importer import MarketItemImporter
from steam_trade_bot.domain.services.sell_history_analyzer import SellHistoryAnalyzer
from steam_trade_bot.domain.services.ste_export import STEExport
from steam_trade_bot.infrastructure.models.market import game_table
from steam_trade_bot.infrastructure.proxy import ProxyRepository
from steam_trade_bot.infrastructure.repositories import GameRepository, MarketItemRepository
from steam_trade_bot.settings import BotSettings


@inject
async def main(
    proxy_rep: ProxyRepository = Provide[Container.repositories.proxy],
) -> None:
    with open('var/proxies.txt', 'r') as f:
        lines = f.readlines()

    lines = [line.strip() for line in lines]

    old_proxies = await proxy_rep.get_all()
    for old_proxy in old_proxies:
        await proxy_rep.remove(old_proxy)

    print(f"Deleted {len(old_proxies)} proxies")

    for line in lines:
        proxy = Proxy.create(line)
        await proxy_rep.add(proxy)

    print(f"Uploaded {len(lines)} proxies")


if __name__ == "__main__":
    container = Container()
    container.config.from_pydantic(BotSettings())
    container.wire(modules=[__name__])

    asyncio.run(main())
