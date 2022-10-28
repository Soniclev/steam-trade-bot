import asyncio
import operator
import re
import urllib.parse
from asyncio import Queue, QueueEmpty
from datetime import datetime, timedelta
from typing import Callable
from urllib.parse import urlparse, parse_qs, urlencode

import python_socks
from aiohttp import ClientSession, ClientError

from steam_trade_bot.domain.entities.market import MarketItem, MarketItemSellHistory, Game, \
    MarketItemInfo, MarketItemNameId
from steam_trade_bot.domain.interfaces.proxy import IProxyProvider, FreeSessionNotFound
from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork
from steam_trade_bot.domain.services.sell_history_analyzer import SellHistoryAnalyzer
from steam_trade_bot.domain.steam_fee import SteamFee


def _retry(func):
    retries = 50

    async def wrapper(*args, **kwargs):
        for _ in range(retries):
            try:
                await func(*args, **kwargs)
                break
            except (ClientError, python_socks._errors.ProxyError):
                await asyncio.sleep(1)
                continue
        else:
            raise MaxRetryReachedException
    return wrapper


class MaxRetryReachedException(Exception):
    pass


class TemporaryImportException(Exception):
    pass


_SEARCH_POSTPONE = timedelta(seconds=15)
_MARKET_ITEM_PAGE_POSTPONE = timedelta(seconds=20)
_ORDER_HISTOGRAM_POSTPONE = timedelta(seconds=5)
_WORKERS = 2


class MarketItemImporter:
    def __init__(
            self,
            unit_of_work: Callable[..., IUnitOfWork],
            sell_history_analyzer: SellHistoryAnalyzer,
            proxy_provider: IProxyProvider,
    ):
        self._uow = unit_of_work
        self._sell_history_analyzer = sell_history_analyzer
        self._proxy_provider = proxy_provider

    async def import_items_from_url(self, url: str):
        # https://steamcommunity.com/market/search/render/?query=&start=20&count=10&search_descriptions=0&sort_column=price&sort_dir=asc&appid=730&category_730_ItemSet%5B%5D=any&category_730_ProPlayer%5B%5D=any&category_730_StickerCapsule%5B%5D=any&category_730_TournamentTeam%5B%5D=any&category_730_Weapon%5B%5D=any&category_730_Type%5B%5D=tag_CSGO_Type_Knife
        start = int(re.findall(r"&start=(\d+)", url)[0])
        count = int(re.findall(r"&count=(\d+)", url)[0])
        norender = "norender=1"

        parsed_url = urlparse(url)
        xxx = parse_qs(parsed_url.query)

        offset = start
        do = True
        while do:
            #xxx['sort_column'] = ["popular"]
            #xxx['sort_dir'] = ["desc"]
            xxx['start'] = [str(offset)]
            xxx['norender'] = ['1']

            new_url = urllib.parse.urlunparse(
                (
                    'https',
                    parsed_url.hostname,
                    parsed_url.path,
                    '',
                    urlencode(xxx, doseq=True),
                    ''  # anchor
                )
            )

            session = await self._get_free_session(_SEARCH_POSTPONE)

            print(f"Loading {new_url}")
            try:
                async with session.get(new_url) as response:
                    response.raise_for_status()
                    resp = await response.json()
            except python_socks._errors.ProxyError:
                await asyncio.sleep(1)
                continue

            if not resp:
                await asyncio.sleep(5)
                continue

            success = resp["success"]

            start = resp["start"]
            total_count = resp["total_count"]

            if not success or total_count == 0:
                continue

            if start > total_count:
                break

            items = resp["results"]

            async with self._uow() as uow:

                apps = {}

                for item in items:
                    app_name = item["app_name"]
                    asset = item["asset_description"]
                    app_id = asset["appid"]

                    if app_id not in apps:
                        apps[app_id] = app_name

                for app_id, app_name in apps.items():
                    if not await uow.game.get(app_id):
                        await uow.game.add(Game(app_id=app_id, name=app_name))

                for item in items:
                    market_hash_name = item["hash_name"]
                    app_name = item["app_name"]
                    sell_listings = item["sell_listings"]
                    sell_price = round(item["sell_price"] / 100, 2)
                    asset = item["asset_description"]
                    app_id = asset["appid"]
                    commodity = asset["commodity"] == 1
                    market_marketable_restriction = asset.get("market_marketable_restriction", None)
                    market_tradable_restriction = asset.get("market_tradable_restriction", None)
                    market_fee = asset.get("market_fee", None)

                    await uow.market_item.add_or_update(
                        MarketItem(
                            app_id=app_id,
                            market_hash_name=market_hash_name,
                            market_fee=market_fee,
                            market_marketable_restriction=market_marketable_restriction,
                            market_tradable_restriction=market_tradable_restriction,
                            commodity=commodity,
                        )
                    )

                    sell_price_no_fee = SteamFee.subtract_fee(sell_price) if sell_price else 0

                    await uow.market_item_info.add_or_update(
                        MarketItemInfo(
                            app_id=app_id,
                            market_hash_name=market_hash_name,
                            currency=1,
                            sell_listings=sell_listings,
                            sell_price=sell_price,
                            sell_price_no_fee=sell_price_no_fee,
                        )
                    )

                offset += count
                await uow.commit()
                print(f"Added or updated {len(items)} items")
        print(resp)

    async def _get_free_session(self, postpone: timedelta) -> ClientSession:
        for _ in range(1000):
            try:
                return await self._proxy_provider.get_session(postpone=postpone)
            except FreeSessionNotFound:
                await asyncio.sleep(0.1)
        else:
            raise FreeSessionNotFound

    async def _get_response(self, url: str, postpone: timedelta):
        session = await self._get_free_session(postpone)

        async with session.get(url) as response:
            response.raise_for_status()
            return response

    async def import_from_all_games(self, currency: int):
        async with self._uow() as uow:
            apps = await uow.game.get_all()

        for game in apps:
            print(f"Importing items from {game=}")
            await self.import_from_db(app_id=game.app_id, currency=currency)

    async def import_from_db(self, app_id: int, currency: int):
        to_import = []
        async with self._uow() as uow:
            market_item_infos = await uow.market_item_info.get_all(app_id, currency)
            # market_item_infos = [x for x in market_item_infos if
            #                      x.sell_price >= 0.1 and x.sell_price < 0.5]
            market_item_infos = sorted(market_item_infos, key=operator.attrgetter('sell_price'))
            for mii in market_item_infos:
                if not await uow.sell_history_analyze_result.get(
                        app_id=mii.app_id,
                        market_hash_name=mii.market_hash_name,
                        currency=mii.currency,
                ):
                    to_import.append(mii)

        queue = Queue()

        for market_item_info in to_import:
            queue.put_nowait(market_item_info)

        await asyncio.gather(
            *[self._run_worker(i+1, queue) for i in range(_WORKERS)]
        )

    async def _run_worker(self, id_: int, queue: Queue):
        while not queue.empty():
            try:
                market_item_info = queue.get_nowait()
            except QueueEmpty:
                break
            print(f"[{id_}] Importing {market_item_info.market_hash_name}")
            try:
                await self.import_item(market_item_info.app_id,
                                       market_item_info.market_hash_name)
            except Exception:
                continue

    @_retry
    async def import_item(self, app_id: int, market_hash_name: str):
        url = f"https://steamcommunity.com/market/listings/{app_id}/{market_hash_name}"

        session = await self._get_free_session(_MARKET_ITEM_PAGE_POSTPONE)

        async with session.get(url) as response:
            response.raise_for_status()
            text = await response.text()
            load_error = re.findall(
                r"<div.+>\s+There was an error getting listings for this item\. Please try again later\.\s+</div>",
                text)
            commodity = re.findall(r"var\s+g_rgAssets\s+=\s+{.*\"commodity\":(\d).*};", text)
            market_fee = re.findall(r"var\s+g_rgAssets\s+=\s+{.*\"market_fee\":(\d).*};", text)
            market_marketable_restriction = re.findall(
                r"var\s+g_rgAssets\s+=\s+{.*\"market_marketable_restriction\":(\d).*};", text
            )
            market_tradable_restriction = re.findall(
                r"var\s+g_rgAssets\s+=\s+{.*\"market_tradable_restriction\":(\d).*};", text
            )
            item_nameid = re.findall(r"Market_LoadOrderSpread\(\s+(\d*)\s+\);", text)
            sell_history = re.findall(r"\s+var line1=([^;]+);", text)

        if load_error:
            raise TemporaryImportException
        timestamp = datetime.now()
        commodity = bool(int(commodity[0]))
        item_nameid = int(item_nameid[0])
        market_fee = float(market_fee[0]) if market_fee else None
        market_marketable_restriction = (
            int(market_marketable_restriction[0]) if market_marketable_restriction else None
        )
        market_tradable_restriction = (
            int(market_tradable_restriction[0]) if market_tradable_restriction else None
        )
        sell_history = (
            sell_history[0] if sell_history else "[]"
        )

        # url = f"https://steamcommunity.com/market/itemordershistogram?country=BY&language=english&currency={1}&item_nameid={item_nameid}&two_factor=0&norender=1"
        #
        # for _ in range(50):
        #     try:
        #         session = await self._get_free_session(_ORDER_HISTOGRAM_POSTPONE)
        #         async with session.get(url) as response:
        #             response.raise_for_status()
        #             text = await response.text()
        #             resp = await response.json()
        #     except python_socks._errors.ProxyError:
        #             await asyncio.sleep(1)
        #             continue
        #
        #     if not resp["success"]:
        #         continue
        #     else:
        #         break

        #buy_orders = {price: count for price, count, _ in resp["buy_order_graph"]}
        #sell_orders = {price: count for price, count, _ in resp["sell_order_graph"]}

        async with self._uow() as uow:
            await uow.market_item.add_or_ignore(
                MarketItem(
                    app_id=app_id,
                    market_hash_name=market_hash_name,
                    market_fee=market_fee,
                    market_marketable_restriction=market_marketable_restriction,
                    market_tradable_restriction=market_tradable_restriction,
                    commodity=commodity,
                )
            )

            history = MarketItemSellHistory(app_id=app_id, market_hash_name=market_hash_name,
                                            currency=1, timestamp=timestamp,
                                            history=sell_history, )
            await uow.sell_history.add(
                history
            )

            analyze_result = await self._sell_history_analyzer.analyze(
                history
            )

            await uow.sell_history_analyze_result.add(analyze_result)

            await uow.market_item_name_id.add(MarketItemNameId(
                app_id=app_id,
                market_hash_name=market_hash_name,
                item_name_id=item_nameid
            ))

            # await uow.market_item_orders.add(MarketItemOrders(
            #     app_id=app_id,
            #     market_hash_name=market_hash_name,
            #     currency=1,
            #     timestamp=timestamp,
            #     dump=text,
            #     buy_count=None,
            #     buy_order=None,
            #     sell_count=None,
            #     sell_order=None,
            #     sell_order_no_fee=None,
            #     )
            # )

            await uow.commit()
