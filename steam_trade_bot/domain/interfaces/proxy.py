from abc import abstractmethod, ABC
from datetime import timedelta

from steam_trade_bot.domain.entities.proxy import Proxy


class FreeProxyNotFound(Exception):
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
    async def get(self, postpone: timedelta) -> Proxy:
        ...

    @abstractmethod
    async def postpone(self, proxy: Proxy, postpone: timedelta) -> None:
        ...
