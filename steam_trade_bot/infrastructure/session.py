import json
from datetime import timedelta
from http.cookies import Morsel

from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from aioredis import Redis

from steam_trade_bot.consts import DEFAULT_CURRENCY
from steam_trade_bot.domain.entities.proxy import Proxy
from steam_trade_bot.domain.interfaces.proxy import IProxyProvider, FreeProxyNotFound
from steam_trade_bot.domain.interfaces.session import (
    AbstractSteamSession,
    ISteamSessionProvider,
    SessionNotFound,
    FreeSessionNotFound,
)


class AnonymousSession(AbstractSteamSession):
    def __init__(self, session: ClientSession):
        self._session = session

    @property
    def session(self) -> ClientSession:
        return self._session

    @property
    def session_id(self) -> str:
        # noinspection PyUnresolvedReferences
        return self._session.cookie_jar._cookies.get("steamcommunity.com")["sessionid"].value

    @property
    def browser_id(self) -> str | None:
        return None

    @property
    def language(self) -> str:
        return "english"

    @property
    def country(self) -> str:
        # noinspection PyUnresolvedReferences
        steam_country = self._session.cookie_jar._cookies.get("steamcommunity.com")[
            "steamCountry"
        ].value
        steam_country = steam_country[:2]

        assert len(steam_country) == 2
        assert steam_country.isupper()

        return steam_country

    @property
    def currency(self) -> int:
        return DEFAULT_CURRENCY


def _steam_session_pattern(proxy: Proxy | None = None):
    if proxy:
        return f"steam:session:{str(proxy)}"
    else:
        return "steam:session:*"


class SteamSessionProvider(ISteamSessionProvider):
    def __init__(self, proxy_provider: IProxyProvider, redis: Redis):
        self._proxy_provider = proxy_provider
        self._redis = redis
        self._pool = {}
        self._session_opener = "https://steamcommunity.com/market/"
        self._session_ttl = timedelta(hours=3)
        self._headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    async def get_free(self, postpone: timedelta) -> AbstractSteamSession:
        try:
            free_proxy = await self._proxy_provider.get(postpone)
        except FreeProxyNotFound as exc:
            raise FreeSessionNotFound from exc
        if free_proxy not in self._pool:
            connector = ProxyConnector.from_url(str(free_proxy), ssl=False)
            self._pool[free_proxy] = AnonymousSession(
                ClientSession(connector=connector, headers=self._headers)
            )

        session_cookies = await self._redis.get(_steam_session_pattern(free_proxy))
        if not session_cookies:
            cookies = []
            async with self._pool[free_proxy].session.get(self._session_opener) as response:
                response.raise_for_status()
                for cookie in response.cookies.values():
                    cookies.append((cookie.key, cookie.value, dict(cookie.items())))
            if cookies:
                await self._redis.set(
                    _steam_session_pattern(free_proxy), json.dumps(cookies), ex=self._session_ttl
                )
        else:
            session_cookies = json.loads(session_cookies.decode())
            morsel_cookies = {}
            for key, value, items in session_cookies:
                cookie = Morsel()
                cookie.set(key, value, value)
                cookie.update(items)
                morsel_cookies[key] = cookie
            self._pool[free_proxy].session.cookie_jar.update_cookies(morsel_cookies)
        return self._pool[free_proxy]

    async def postpone(self, session: AbstractSteamSession, postpone: timedelta) -> None:
        for proxy, session_ in self._pool.items():
            if session is session_:
                await self._proxy_provider.postpone(proxy, postpone)
                break
        else:
            raise SessionNotFound
