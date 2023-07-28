import random
from datetime import timedelta
from typing import Callable

from aioredis import Redis
from sqlalchemy import insert, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from steam_trade_bot.domain.entities.proxy import Proxy
from steam_trade_bot.domain.interfaces.proxy import (
    IProxyRepository,
    IProxyProvider,
    FreeProxyNotFound,
)
from steam_trade_bot.infrastructure.models.proxy import proxy_table


class ProxyRepository(IProxyRepository):
    def __init__(self, session: Callable[..., AsyncSession]):
        self._session = session

    async def add(self, proxy: Proxy):
        async with self._session() as session:
            await session.execute(insert(proxy_table).values(proxy.dict()))
            await session.commit()

    async def remove(self, proxy: Proxy):
        async with self._session() as session:
            await session.execute(
                delete(proxy_table)
                .where(proxy_table.c.protocol == proxy.protocol)
                .where(proxy_table.c.host == proxy.host)
                .where(proxy_table.c.port == proxy.port)
                .where(proxy_table.c.login == proxy.login)
                .where(proxy_table.c.password == proxy.password)
            )
            await session.commit()

    async def get_all(self) -> list[Proxy]:
        async with self._session() as session:
            result = await session.execute(
                select(
                    [
                        proxy_table.c.protocol,
                        proxy_table.c.host,
                        proxy_table.c.port,
                        proxy_table.c.login,
                        proxy_table.c.password,
                    ]
                )
            )
            rows = result.fetchall()
            return [Proxy(**row) for row in rows]


def _proxy_pattern(proxy: Proxy | None = None):
    if proxy:
        return f"locks:proxies:{str(proxy)}"
    else:
        return "locks:proxies:*"


class ProxyProvider(IProxyProvider):
    def __init__(self, proxy_rep: IProxyRepository, redis: Redis):
        self._proxy_rep = proxy_rep
        self._redis = redis

    async def get(self, postpone: timedelta) -> Proxy:
        proxies = await self._proxy_rep.get_all()
        random.shuffle(proxies)
        keys = [key.decode() for key in await self._redis.keys(_proxy_pattern())]
        for proxy in proxies:
            if _proxy_pattern(proxy) in keys:
                continue
            if await self._redis.set(_proxy_pattern(proxy), value="", ex=postpone):
                free_proxy = proxy
                break
        else:
            raise FreeProxyNotFound

        return free_proxy

    async def postpone(self, proxy: Proxy, postpone: timedelta) -> None:
        await self._redis.set(_proxy_pattern(proxy), value="", ex=postpone)
