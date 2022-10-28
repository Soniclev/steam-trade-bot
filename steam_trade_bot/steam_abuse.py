import asyncio
import logging
import urllib.parse
from datetime import datetime, timedelta

from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from dependency_injector.wiring import inject


from steam_trade_bot.containers import Container
from steam_trade_bot.domain.entities.proxy import Proxy
from steam_trade_bot.settings import BotSettings


_log = logging.getLogger(__name__)


@inject
async def main() -> None:
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        # 'X-Requested-With': 'XMLHttpRequest',
        "Connection": "keep-alive",
        # 'Referer': referer,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        # 'If-Modified-Since': time_now
    }
    proxy = Proxy.create("")
    connector = ProxyConnector.from_url(str(proxy), ssl=False)
    session = ClientSession(connector=connector, headers=_headers)
    url = "https://steamcommunity.com/market/listings/730/Sticker%20%7C%20Gambit%20Gaming%20%28Holo%29%20%7C%20Stockholm%202021"
    app_id = 730
    market_hash_name = "Sticker | Gambit Gaming (Holo) | Stockholm 2021"
    item_name_id = 176269942
    async with session.get(url) as response:
        response.raise_for_status()
        text = await response.text()
    url = f"https://steamcommunity.com/market/itemordershistogram?country=NL&language=russian&currency=1&item_nameid={item_name_id}&two_factor=0"
    time_now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    headers = {
        "Origin": "steamcommunity.com",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://steamcommunity.com/market/listings/{app_id}/{urllib.parse.quote(market_hash_name)}",
        "If-Modified-Since": time_now,
    }
    for i in range(1, 501):
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            _log.info(response.request_info.headers)
            _log.info(response.headers)
            _log.info(response.cookies)
            date = response.headers["Date"]
            date_dt = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S GMT")
            expires = response.headers["Expires"]
            expires_dt = datetime.strptime(expires, "%a, %d %b %Y %H:%M:%S GMT")
            if expires_dt > date_dt:
                sleep = expires_dt - date_dt
                if sleep < timedelta(seconds=5):
                    sleep = timedelta(seconds=5)
            else:
                sleep = timedelta(seconds=5)
            last_modified = response.headers["Last-Modified"]
            text = await response.text()
            if text:
                _log.info(f"[Step {i}] OK")
            elif response.status == 304:
                _log.info(f"[Step {i}] 304 OK")

            time_now = last_modified
            headers["If-Modified-Since"] = time_now

        await asyncio.sleep(sleep.total_seconds())


if __name__ == "__main__":
    container = Container()
    container.config.from_pydantic(BotSettings())
    container.wire(modules=[__name__])

    asyncio.run(main())
