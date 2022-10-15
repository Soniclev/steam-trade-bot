import re
from datetime import datetime

from aiohttp import ClientSession

from steam_trade_bot.domain.entities.market import MarketItem, MarketItemSellHistory
from steam_trade_bot.infrastructure.repositories import MarketItemRepository, \
    MarketItemSellHistoryRepository


class MarketItemImporter:
    def __init__(self, market_item_rep: MarketItemRepository,
                 market_item_sell_history_rep: MarketItemSellHistoryRepository):
        self._market_item_rep = market_item_rep
        self._market_item_sell_history_rep = market_item_sell_history_rep

    async def import_item(self, app_id: int, market_hash_name: str):
        url = f"https://steamcommunity.com/market/listings/{app_id}/{market_hash_name}"
        async with ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                text = await response.text()
                commodity = re.findall(r"var\s+g_rgAssets\s+=\s+{.*\"commodity\":(\d).*};",
                                       text)
                market_fee = re.findall(r"var\s+g_rgAssets\s+=\s+{.*\"market_fee\":(\d).*};",
                                       text)
                market_marketable_restriction = re.findall(r"var\s+g_rgAssets\s+=\s+{.*\"market_marketable_restriction\":(\d).*};",
                                        text)
                market_tradable_restriction = re.findall(r"var\s+g_rgAssets\s+=\s+{.*\"market_tradable_restriction\":(\d).*};",
                                        text)
                item_nameid = re.findall(r"Market_LoadOrderSpread\(\s+(\d*)\s+\);", text)
                sell_history = re.findall(r"\s+var line1=([^;]+);", text)[0]

        commodity = bool(int(commodity[0]))
        item_nameid = int(item_nameid[0])
        market_fee = float(market_fee[0]) if market_fee else None
        market_marketable_restriction = int(market_marketable_restriction[0]) if market_marketable_restriction else None
        market_tradable_restriction = int(market_tradable_restriction[0]) if market_tradable_restriction else None

        await self._market_item_rep.add(
            MarketItem(
                app_id=app_id,
                market_hash_name=market_hash_name,
                market_fee=market_fee,
                market_marketable_restriction=market_marketable_restriction,
                market_tradable_restriction=market_tradable_restriction,
                commodity=commodity,
                item_name_id=item_nameid
            )
        )

        await self._market_item_sell_history_rep.add(
            MarketItemSellHistory(
                app_id=app_id,
                market_hash_name=market_hash_name,
                currency=1,
                timestamp=datetime.now(),
                history=sell_history
            )
        )
