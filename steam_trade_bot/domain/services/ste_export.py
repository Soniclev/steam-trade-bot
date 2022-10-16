import sqlite3
from pathlib import Path

from steam_trade_bot.domain.steam_fee import SteamFee
from steam_trade_bot.infrastructure.repositories import (
    SellHistoryAnalyzeResultRepository,
    MarketItemRepository,
)


class STEExport:
    def __init__(
        self,
        market_item_rep: MarketItemRepository,
        sell_history_analyze_result_rep: SellHistoryAnalyzeResultRepository,
    ):
        self._market_item_rep = market_item_rep
        self._sell_history_analyze_result_rep = sell_history_analyze_result_rep

    async def export(self, path: Path):
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        # cur.execute("SELECT * FROM item;")
        result = await self._sell_history_analyze_result_rep.get(
            app_id=730, market_hash_name="Stockholm 2021 Mirage Souvenir Package", currency=1
        )
        market_item = await self._market_item_rep.get(
            app_id=730, market_hash_name="Stockholm 2021 Mirage Souvenir Package"
        )
        market_url = f"https://steamcommunity.com/market/listings/{market_item.app_id}/{market_item.market_hash_name}"
        buy_order = SteamFee.subtract_fee(result.sell_order - 0.03)
        buy_order = str(int(buy_order * 100))
        sell_order = str(int(result.sell_order * 100))
        cur.executemany(
            r'INSERT INTO "main"."item" ("name", "type", "sort", "url", "market_hash_name", "item_nameid", "appid", "contextid", "id_group", "b_cnt", "b", "b_on", "s", "s_on", "order_date") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);',
            [
                (
                    market_item.market_hash_name,
                    None,
                    "0",
                    market_url,
                    market_item.market_hash_name,
                    market_item.item_name_id,
                    market_item.app_id,
                    "2",
                    "0",
                    "1",
                    buy_order,
                    "0",
                    sell_order,
                    "0",
                    None,
                ),
            ],
        )
        conn.commit()
