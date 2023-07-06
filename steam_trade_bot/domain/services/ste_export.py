import operator
import sqlite3
from pathlib import Path

from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork
from steam_trade_bot.domain.steam_fee import SteamFee


class STEExport:
    def __init__(
        self,
        unit_of_work: IUnitOfWork,
    ):
        self._unit_of_work = unit_of_work

    async def export(self, path: Path):
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        # cur.execute("SELECT * FROM item;")
        items = await self._market_item_rep.get_all(app_id=730)
        for market_item in items:
            result = await self._sell_history_analyze_result_rep.get(
                app_id=market_item.app_id, market_hash_name=market_item.market_hash_name
            )

            if not result or not result.recommended:
                continue

            market_url = f"https://steamcommunity.com/market/listings/{market_item.app_id}/{market_item.market_hash_name}"
            profit = round(min(0.01, result.sell_order * 0.05), 2)
            buy_order = SteamFee.subtract_fee(result.sell_order - profit)
            buy_order = str(int(buy_order * 100))
            sell_order = SteamFee.subtract_fee(result.sell_order)
            sell_order = str(int(sell_order * 100))
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
