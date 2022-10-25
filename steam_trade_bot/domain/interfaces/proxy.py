from abc import abstractmethod, ABC
from datetime import timedelta

from aiohttp import ClientSession

from steam_trade_bot.domain.entities.proxy import Proxy


class FreeSessionNotFound(Exception):
    pass


class IProxyRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[Proxy]:
        ...

    @abstractmethod
    async def add(self, proxy: Proxy) -> None:
        ...

    @abstractmethod
    async def remove(self, proxy: Proxy) -> None:
        ...


class IProxyProvider(ABC):
    @abstractmethod
    async def get_session(self, postpone: timedelta) -> ClientSession:
        ...
