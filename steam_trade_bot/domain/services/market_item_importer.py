import asyncio
import itertools
import logging
import re
import urllib.parse
from asyncio import Queue, QueueEmpty
from datetime import datetime, timedelta
from math import ceil
from operator import attrgetter
from typing import Callable
from urllib.parse import urlparse, parse_qs, urlencode

from aiohttp import ClientResponseError

from steam_trade_bot.consts import DEFAULT_CURRENCY
from steam_trade_bot.domain.exceptions import SerializationError

from steam_trade_bot.domain.entities.market import (
    MarketItem,
    MarketItemSellHistory,
    MarketItemInfo,
    MarketItemNameId,
    MarketItemOrder,
    MarketItemOrders,
)
from steam_trade_bot.domain.entities.game import Game
from steam_trade_bot.domain.exceptions import CurrencyNotSupported, ItemNameIdNotFound
from steam_trade_bot.domain.interfaces.session import (
    AbstractSteamSession,
    ISteamSessionProvider,
    FreeSessionNotFound,
)
from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork
from steam_trade_bot.domain.services.sell_history_analyzer import SellHistoryAnalyzer
from steam_trade_bot.domain.steam_fee import SteamFee
from steam_trade_bot.settings import (
    MarketItemOrdersHistogramSettings,
    MarketItemPageSettings,
    MarketItemSearchSettings,
)

_log = logging.getLogger(__name__)


def _parse_orders(data: dict) -> tuple[list[MarketItemOrder], list[MarketItemOrder]]:
    def _load_from_graph(graph, orders):
        last_quantity = 0
        for price, quantity, _ in graph:
            if price not in orders:
                orders[price] = MarketItemOrder(price=price, quantity=quantity - last_quantity)
            last_quantity = quantity

    buy_orders = {}
    sell_orders = {}
    _load_from_graph(data["buy_order_graph"], buy_orders)
    _load_from_graph(data["sell_order_graph"], sell_orders)

    return sorted(buy_orders.values(), key=attrgetter("price"), reverse=True), sorted(
        sell_orders.values(), key=attrgetter("price"), reverse=False
    )


class MaxRetryReachedException(Exception):
    pass


class TemporaryImportException(Exception):
    pass


class NoListingsException(Exception):
    def __init__(self, app_id: int, market_hash_name: str):
        self.app_id = app_id
        self.market_hash_name = market_hash_name
        super().__init__(f"There are no listings for {app_id=} {market_hash_name=}")


class InvalidMarketItemException(Exception):
    def __init__(self, app_id: int, market_hash_name: str):
        self.app_id = app_id
        self.market_hash_name = market_hash_name
        super().__init__(f"Invalid market item definition {app_id=} {market_hash_name=}")


def _recreate_url(parsed_query: dict, parsed_url: urllib.parse.ParseResult) -> str:
    new_url = urllib.parse.urlunparse(
        (
            "https",
            parsed_url.hostname,
            parsed_url.path,
            "",
            urlencode(parsed_query, doseq=True),
            "",  # anchor
        )
    )
    return new_url


class BaseMarketItemImporter:
    def __init__(
            self,
            unit_of_work: Callable[..., IUnitOfWork],
            steam_session_provider: ISteamSessionProvider,
    ):
        self._steam_session_provider = steam_session_provider
        self._uow = unit_of_work

    async def _get_free_session(
            self, postpone: timedelta, attempts: int = 1000
    ) -> AbstractSteamSession:
        for _ in range(attempts):
            try:
                return await self._steam_session_provider.get_free(postpone=postpone)
            except FreeSessionNotFound:
                await asyncio.sleep(0.1)
        raise FreeSessionNotFound

    async def _get_response(
            self,
            url: str,
            postpone: timedelta,
            max_retries: int = 50,
            delay: timedelta = timedelta(seconds=1),
    ):
        headers = {
            "Origin": "steamcommunity.com",
            "X-Requested-With": "XMLHttpRequest",
            "X-Prototype-Version": "1.7",
            "Referer": "https://steamcommunity.com/market/",
        }
        for _ in range(max_retries):
            steam_session = await self._get_free_session(postpone)
            _log.info(f"Loading {url}")
            try:
                async with steam_session.session.get(url, headers=headers, timeout=10) as response:
                    response.raise_for_status()
                    await response.text()
                    return response
            except Exception:
                await asyncio.sleep(delay.total_seconds())
                continue
        raise FreeSessionNotFound


class MarketItemImporterFromSearch(BaseMarketItemImporter):
    def __init__(
            self,
            uow: Callable[..., IUnitOfWork],
            steam_session_provider: ISteamSessionProvider,
            settings: dict,
    ):
        super(MarketItemImporterFromSearch, self).__init__(uow, steam_session_provider)
        self._settings = MarketItemSearchSettings(**settings)

    async def import_items_from_url(self, url: str, currency: int = DEFAULT_CURRENCY):
        # https://steamcommunity.com/market/search/render/?query=&start=20&count=10
        # &search_descriptions=0&sort_column=price&sort_dir=asc&appid=730
        parsed_url = urlparse(url)
        parsed_query = parse_qs(parsed_url.query)
        start = int(parsed_query["start"][0])
        count = int(parsed_query["count"][0])
        offset_gen = itertools.count(start, count)
        offset = next(offset_gen)

        new_url = self._build_url(offset, parsed_query, parsed_url)
        response = await self._get_response(
            new_url,
            self._settings.postpone,
            max_retries=self._settings.max_retries,
            delay=self._settings.retry_delay,
        )
        resp = await response.json()

        success = resp["success"]
        total_count = resp["total_count"]
        if not success:
            raise TemporaryImportException

        queue = Queue()
        queue.put_nowait((new_url, currency))
        steps = ceil(total_count / count)
        for _ in range(steps):
            offset = next(offset_gen)
            new_url = self._build_url(offset, parsed_query, parsed_url)
            queue.put_nowait((new_url, currency))

        await asyncio.gather(
            *[
                self._run_import_worker(i + 1, queue)
                for i in range(self._settings.workers)
            ]
        )

    async def _run_import_worker(self, id_: int, queue: Queue):
        while not queue.empty():
            try:
                url, currency = queue.get_nowait()
            except QueueEmpty:
                break
            _log.info(f"[{id_}] Importing {url=}")
            try:
                await self.load_search_results(
                    url, currency
                )
            except Exception as exc:
                _log.exception(exc)
                continue

    async def load_search_results(self, url: str, currency: int):
        for _ in range(10):
            response = await self._get_response(
                url,
                self._settings.postpone,
                max_retries=self._settings.max_retries,
                delay=self._settings.retry_delay,
            )
            resp = await response.json()

            # some temporary issue with certain offset
            if not resp:
                await asyncio.sleep(10)
                continue

            success = resp["success"]
            total_count = resp["total_count"]
            if not success or total_count == 0:
                continue

            break
        else:
            raise TemporaryImportException
        await self._process_response(resp, currency)

    async def _process_response(self, resp: dict, currency: int):
        items = resp["results"]
        apps = {item["asset_description"]["appid"]: item["app_name"] for item in items}
        games = [Game(app_id=app_id, name=app_name) for app_id, app_name in apps.items()]
        async with self._uow() as uow:
            await uow.game.add_or_ignore(games)
            await uow.commit()

        market_items = []
        market_item_infos = []
        for item in items:
            market_hash_name = item["hash_name"]
            sell_listings = item["sell_listings"]
            sell_price = round(item["sell_price"] / 100, 2)
            asset = item["asset_description"]
            app_id = asset["appid"]
            commodity = asset["commodity"] == 1
            market_marketable_restriction = asset.get("market_marketable_restriction", None)
            market_tradable_restriction = asset.get("market_tradable_restriction", None)
            market_fee = asset.get("market_fee", None)
            sell_price_no_fee = SteamFee.subtract_fee(sell_price) if sell_price else None

            market_items.append(
                MarketItem(
                    app_id=app_id, market_hash_name=market_hash_name,
                    market_fee=market_fee,
                    market_marketable_restriction=market_marketable_restriction,
                    market_tradable_restriction=market_tradable_restriction,
                    commodity=commodity,
                )
            )

            market_item_infos.append(
                MarketItemInfo(
                    app_id=app_id, market_hash_name=market_hash_name,
                    sell_listings=sell_listings,
                    sell_price=sell_price,
                    sell_price_no_fee=sell_price_no_fee,
                )
            )

        for _ in range(100):
            try:
                async with self._uow() as uow:
                    await uow.market_item.add_or_update(market_items)
                    await uow.market_item_info.add_or_update(market_item_infos)
                    await uow.commit()
                    _log.info(f"Updated {len(items)} items")
                    break
            except SerializationError:
                _log.info("SerializationError, trying to again to save")
                await uow.rollback()

    def _build_url(self, offset, parsed_query, parsed_url):
        parsed_query["sort_column"] = ["quantity"]
        parsed_query["sort_dir"] = ["desc"]
        parsed_query["norender"] = ["1"]
        parsed_query["start"] = [str(offset)]
        new_url = _recreate_url(parsed_query, parsed_url)
        return new_url


class MarketItemImporterFromPage(BaseMarketItemImporter):
    def __init__(
            self,
            unit_of_work: Callable[..., IUnitOfWork],
            sell_history_analyzer: SellHistoryAnalyzer,
            steam_session_provider: ISteamSessionProvider,
            settings: dict,
    ):
        super().__init__(unit_of_work, steam_session_provider)
        self._sell_history_analyzer = sell_history_analyzer
        self._settings = MarketItemPageSettings(**settings)

    async def import_from_all_games(self, currency: int):
        async with self._uow() as uow:
            apps = await uow.game.get_all()
            await uow.commit()

        for game in apps:
            _log.info(f"Importing items from {game=}")
            await self.import_from_db(app_id=game.app_id, currency=currency)

    async def update_all_games(self, currency: int, older: datetime | None = None):
        async with self._uow() as uow:
            apps = await uow.game.get_all()
            await uow.commit()

        for game in apps:
            _log.info(f"Updating items from {game=}")
            await self.update_from_db(app_id=game.app_id, currency=currency, older=older)

    async def import_from_db(self, app_id: int, currency: int):
        to_import = []
        async with self._uow() as uow:
            market_item_infos = {mii.market_hash_name: mii for mii in
                                 await uow.market_item_info.get_all(app_id, currency)}
            existed_market_names = set(market_item_infos.keys())
            async for results in uow.sell_history_analyze_result.yield_all(
                    app_id=app_id,
                    currency=currency,
                    count=1000,
            ):
                market_names = set(map(attrgetter('market_hash_name'), results))
                to_import.extend([market_item_infos[x] for x in market_names-existed_market_names])
            await uow.commit()

        queue = Queue()

        for market_item_info in to_import:
            queue.put_nowait(market_item_info)

        await asyncio.gather(
            *[
                self._run_import_item_worker(i + 1, queue, currency)
                for i in range(self._settings.workers)
            ]
        )

    async def update_from_db(self, app_id: int, currency: int, older: datetime | None = None):
        to_import = []
        async with self._uow() as uow:
            market_item_infos = {mii.market_hash_name: mii for mii in
                                 await uow.market_item_info.get_all(app_id, currency)}
            async for results in uow.sell_history_analyze_result.yield_all(
                    app_id=app_id,
                    currency=currency,
                    count=1000,
            ):
                for result in results:
                    if older and result.timestamp >= older:
                        continue
                    if result.market_hash_name not in market_item_infos:
                        continue
                    mii = market_item_infos[result.market_hash_name]
                    to_import.append((mii, result.timestamp))
            await uow.commit()

        sorted_to_import = sorted(market_item_infos, key=lambda x: x[1])

        queue = Queue()

        for market_item_info in sorted_to_import:
            queue.put_nowait(market_item_info)

        await asyncio.gather(
            *[
                self._run_import_item_worker(i + 1, queue, currency)
                for i in range(self._settings.workers)
            ]
        )

    async def _run_import_item_worker(self, id_: int, queue: Queue, currency: int):
        while not queue.empty():
            try:
                market_item_info = queue.get_nowait()
            except QueueEmpty:
                break
            _log.info(
                f"[{id_}] Processing {market_item_info.app_id} - {market_item_info.market_hash_name}")
            try:
                await self.import_item(
                    market_item_info.app_id, market_item_info.market_hash_name, currency
                )
            except (NoListingsException, InvalidMarketItemException) as exc:
                if isinstance(exc, NoListingsException):
                    _log.info(
                        f"No listings for for {exc.app_id} - {exc.market_hash_name}. Deleting this market item")
                elif isinstance(exc, InvalidMarketItemException):
                    _log.info(
                        f"Found invalid market item definition {exc.app_id} - {exc.market_hash_name}. Deleting this market item")
                async with self._uow() as uow:
                    await uow.market_item.remove(app_id=exc.app_id,
                                                 market_hash_name=exc.market_hash_name)
                    await uow.commit()
                _log.info(f"Successfully deleted market item {exc.app_id} - {exc.market_hash_name}")
            except Exception as exc:
                _log.exception(exc)
                continue

    async def import_item(self, app_id: int, market_hash_name: str, currency: int):
        url = f"https://steamcommunity.com/market/listings/{app_id}/{urllib.parse.quote(market_hash_name)}"
        steam_session = await self._get_free_session(self._settings.postpone)
        if steam_session.currency != currency:
            raise CurrencyNotSupported(currency)

        try:
            async with steam_session.session.get(url) as response:
                response.raise_for_status()
                text = await response.text()
        except ClientResponseError as exc:
            if exc.status == 429:
                _log.error(
                    f"Postponing session for {self._settings.too_many_requests_postpone}"
                )
                await self._steam_session_provider.postpone(
                    steam_session, self._settings.too_many_requests_postpone
                )
                raise TemporaryImportException
            elif exc.status == 404:
                raise InvalidMarketItemException(app_id=app_id,
                                                 market_hash_name=market_hash_name) from exc
            else:
                raise

        load_error = re.findall(
            r"<div.+>\s+There was an error getting listings for this item\. Please try again later\.\s+</div>",
            text,
        )
        no_listings = re.findall(r"<div.+>\s+There are no listings for this item\.\s+</div>", text)
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
        if no_listings and not item_nameid:
            raise NoListingsException(app_id=app_id, market_hash_name=market_hash_name)
        if commodity and not item_nameid:
            raise InvalidMarketItemException(app_id=app_id, market_hash_name=market_hash_name)
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
        sell_history = sell_history[0] if sell_history else "[]"

        history = MarketItemSellHistory(
            app_id=app_id,
            market_hash_name=market_hash_name,
            currency=currency,
            timestamp=timestamp,
            history=sell_history,
        )

        analyze_result = await self._sell_history_analyzer.analyze(history)
        market_item = MarketItem(
            app_id=app_id,
            market_hash_name=market_hash_name,
            market_fee=market_fee,
            market_marketable_restriction=market_marketable_restriction,
            market_tradable_restriction=market_tradable_restriction,
            commodity=commodity,
        )
        item_name_id = MarketItemNameId(
            app_id=app_id, market_hash_name=market_hash_name, item_name_id=item_nameid
        )
        async with self._uow() as uow:
            await uow.market_item.add_or_update([market_item])
            await uow.sell_history.add_or_update([history])
            await uow.sell_history_analyze_result.add_or_update([analyze_result])
            await uow.market_item_name_id.add_or_ignore([item_name_id])
            await uow.commit()
        _log.info(f"[{market_hash_name}] OK")


class MarketItemImporterFromOrdersHistogram(BaseMarketItemImporter):
    def __init__(
            self,
            uow: Callable[..., IUnitOfWork],
            steam_session_provider: ISteamSessionProvider,
            settings: dict,
    ):
        super(MarketItemImporterFromOrdersHistogram, self).__init__(uow, steam_session_provider)
        self._settings = MarketItemOrdersHistogramSettings(**settings)

    async def import_orders_from_all_games(self, currency: int):
        async with self._uow() as uow:
            apps = await uow.game.get_all()
            await uow.commit()

        for game in apps:
            _log.info(f"Importing items orders from {game=}")
            await self.import_orders_from_db(app_id=game.app_id, currency=currency)

    async def import_orders_from_db(self, app_id: int, currency: int):
        to_import = []
        async with self._uow() as uow:
            market_item_ids = {
                mii.market_hash_name: mii
                for mii in await uow.market_item_name_id.get_all(app_id)
            }
            existed_market_names = set(market_item_ids.keys())
            async for results in uow.market_item_orders.yield_all(
                    app_id=app_id,
                    currency=currency,
                    count=1000,
                ):
                market_names = set(map(attrgetter('market_hash_name'), results))
                to_import.extend([market_item_ids[x] for x in market_names-existed_market_names])

            await uow.commit()

        queue = Queue()

        for market_item_info in to_import:
            queue.put_nowait(market_item_info)

        await asyncio.gather(
            *[
                self._run_import_item_orders_worker(i + 1, queue, currency)
                for i in range(self._settings.workers)
            ]
        )

    async def update_orders(self, currency: int, older: datetime | None = None):
        async with self._uow() as uow:
            apps = await uow.game.get_all()
            await uow.commit()

        for game in apps:
            _log.info(f"Updating items orders from {game=}")
            await self.update_orders_from_db(app_id=game.app_id, currency=currency, older=older)

    async def update_orders_from_db(self, app_id: int, currency: int, older: datetime | None = None):
        to_import = []
        async with self._uow() as uow:
            market_item_ids = {
                mii.market_hash_name: mii
                for mii in await uow.market_item_name_id.get_all(app_id)
            }
            async for results in uow.market_item_orders.yield_all(
                    app_id=app_id,
                    currency=currency,
                    count=1000,
                ):
                for result in results:
                    if older and result.timestamp >= older:
                        continue
                    if result.market_hash_name not in market_item_ids:
                        continue
                    mii = market_item_ids[result.market_hash_name]
                    to_import.append((mii, result.timestamp))

            await uow.commit()

        sorted_to_import = sorted(to_import, key=lambda x: x[1])

        queue = Queue()

        for market_item_info, timestamp in sorted_to_import:
            queue.put_nowait(market_item_info)

        await asyncio.gather(
            *[
                self._run_import_item_orders_worker(i + 1, queue, currency)
                for i in range(self._settings.workers)
            ]
        )

    async def _run_import_item_orders_worker(self, id_: int, queue: Queue, currency: int):
        while not queue.empty():
            try:
                market_item_info = queue.get_nowait()
            except QueueEmpty:
                break
            _log.info(
                f"[{id_}] Processing item orders {market_item_info.app_id} - {market_item_info.market_hash_name}")
            try:
                await self.import_item_orders(
                    market_item_info.app_id, market_item_info.market_hash_name, currency
                )
            except Exception as exc:
                _log.exception(exc)
                continue

    async def import_item_orders(self, app_id: int, market_hash_name: str, currency: int):
        async with self._uow() as uow:
            item_name_id = await uow.market_item_name_id.get(app_id, market_hash_name)
            if not item_name_id:
                raise ItemNameIdNotFound(app_id, market_hash_name)
            await uow.commit()

        item_name_id = item_name_id.item_name_id

        steam_session = await self._get_free_session(self._settings.postpone)
        if steam_session.currency != currency:
            raise CurrencyNotSupported(currency)
        country = steam_session.country
        language = steam_session.language

        url = (
            f"https://steamcommunity.com/market/itemordershistogram?country={country}"
            f"&language={language}&currency={currency}&item_nameid={item_name_id}&two_factor=0"
        )

        fake_cache_delay = timedelta(seconds=6)
        time_now = datetime.utcnow() - fake_cache_delay
        headers = {
            "Origin": "steamcommunity.com",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://steamcommunity.com/market/listings/{app_id}/{urllib.parse.quote(market_hash_name)}",
            "If-Modified-Since": time_now.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        }
        max_retries = 10
        timeout = self._settings.timeout.total_seconds()
        minimal_request_delay = self._settings.minimal_delay
        for i in range(max_retries):
            try:
                _log.info(f"Request {url}")
                async with steam_session.session.get(
                        url, headers=headers, timeout=timeout
                ) as response:
                    response.raise_for_status()
                    date = datetime.strptime(response.headers["Date"], "%a, %d %b %Y %H:%M:%S GMT")
                    expires = datetime.strptime(
                        response.headers["Expires"], "%a, %d %b %Y %H:%M:%S GMT"
                    )

                    sleep = minimal_request_delay
                    if expires > date and expires - date > sleep:
                        sleep = expires - date

                    last_modified = response.headers["Last-Modified"]
                    headers["If-Modified-Since"] = last_modified
                    text = await response.text()
                    if text:
                        _log.info(f"[Step {i}][{market_hash_name}] OK")
                    elif response.status == 304:
                        _log.info(f"[Step {i}][{market_hash_name}] 304 OK")

                    if response.status == 304:
                        await asyncio.sleep(sleep.total_seconds())
                        continue
                    elif response.status == 200:
                        json = await response.json()
                        if not json["success"]:
                            await asyncio.sleep(sleep.total_seconds())
                            continue
                        break
            except ClientResponseError as exc:
                if exc.status == 429:
                    _log.error(
                        f"Postponing session for {self._settings.too_many_requests_postpone}"
                    )
                    await self._steam_session_provider.postpone(
                        steam_session, self._settings.too_many_requests_postpone
                    )
                raise
        timestamp = datetime.now()
        sell_summary = re.findall(
            r"<span class=\"market_commodity_orders_header_promote\">(\d+)</span> for sale starting",
            json["sell_order_summary"],
        )
        if sell_summary:
            total_sell_listings = int(sell_summary[0])
        else:
            total_sell_listings = 0
        buy_orders, sell_orders = _parse_orders(json)
        buy_order = buy_orders[0] if buy_orders else None
        buy_count = buy_order.quantity if buy_order else None
        buy_price = buy_order.price if buy_order else None
        sell_order = sell_orders[0] if sell_orders else None
        sell_count = sell_order.quantity if sell_order else None
        sell_price = sell_order.price if sell_order else None
        sell_price_no_fee = SteamFee.subtract_fee(sell_price) if sell_price else None
        market_item_orders = MarketItemOrders(
            app_id=app_id,
            market_hash_name=market_hash_name,
            currency=currency,
            timestamp=timestamp,
            dump=text,
            buy_count=buy_count,
            buy_order=buy_price,
            sell_count=sell_count,
            sell_order=sell_price,
            sell_order_no_fee=sell_price_no_fee,
        )

        market_item_info = MarketItemInfo(
            app_id=app_id,
            market_hash_name=market_hash_name,
            currency=currency,
            sell_listings=total_sell_listings,
            sell_price=sell_price,
            sell_price_no_fee=sell_price_no_fee,
        )

        async with self._uow() as uow:
            await uow.market_item_info.add_or_update([market_item_info])
            await uow.market_item_orders.add_or_update([market_item_orders])
            await uow.commit()
