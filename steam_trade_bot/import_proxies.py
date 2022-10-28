import asyncio
import logging

from dependency_injector.wiring import Provide, inject

from steam_trade_bot.containers import Container
from steam_trade_bot.domain.entities.proxy import Proxy
from steam_trade_bot.infrastructure.proxy import ProxyRepository
from steam_trade_bot.settings import BotSettings


_log = logging.getLogger(__name__)


@inject
async def main(
    proxy_rep: ProxyRepository = Provide[Container.repositories.proxy],
) -> None:
    with open("var/proxies.txt", "r") as f:
        lines = f.readlines()

    lines = [line.strip() for line in lines]

    old_proxies = await proxy_rep.get_all()
    for old_proxy in old_proxies:
        await proxy_rep.remove(old_proxy)

    _log.info(f"Deleted {len(old_proxies)} proxies")

    for line in lines:
        proxy = Proxy.create(line)
        await proxy_rep.add(proxy)

    _log.info(f"Uploaded {len(lines)} proxies")


if __name__ == "__main__":
    container = Container()
    container.config.from_pydantic(BotSettings())
    container.wire(modules=[__name__])

    asyncio.run(main())
