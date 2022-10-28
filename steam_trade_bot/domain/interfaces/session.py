from abc import ABC, abstractmethod
from datetime import timedelta

from aiohttp import ClientSession


class AbstractSteamSession(ABC):
    @property
    @abstractmethod
    def session(self) -> ClientSession:
        ...

    @property
    @abstractmethod
    def session_id(self) -> str:
        ...

    @property
    @abstractmethod
    def browser_id(self) -> str | None:
        ...

    @property
    @abstractmethod
    def language(self) -> str:
        ...

    @property
    @abstractmethod
    def country(self) -> str:
        ...

    @property
    @abstractmethod
    def currency(self) -> int:
        ...


class ISteamSessionProvider(ABC):
    @abstractmethod
    async def get_free(self, postpone: timedelta) -> AbstractSteamSession:
        ...

    @abstractmethod
    async def postpone(self, session: AbstractSteamSession, postpone: timedelta) -> None:
        ...


class FreeSessionNotFound(Exception):
    pass


class SessionNotFound(Exception):
    pass
