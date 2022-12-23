import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from steam_trade_bot.domain.entities.market import MarketItemOrders, SellHistoryAnalyzeResult, \
    MarketItemOrder, MarketItemSellHistory
from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork
from steam_trade_bot.domain.services.market_item_importer import _parse_orders
from steam_trade_bot.domain.services.sell_history_analyzer import steam_date_str_to_datetime

"""
timestamp: 2022-11-12 21:17:43.821 +0300
items:
- "★ Huntsman Knife | Freehand (Minimal Wear)":
    timestamp: 2022-11-12 21:16:43.821 +0300
    buy_order: 110.51
    sell_order: 135.26
    sell_order_no_fee: 121.58
    profit: 11.07
    sells_history:
      day: 
        {all: 2, buy_desired: 1, sell_desired: 0}
      week: 
        {all: 7, buy_desired: 3, sell_desired: 0}
      month:
        {all: 30, buy_desired: 10, sell_desired: 0}
    buy_orders_before_desired: 3
    sell_orders_before_desired: 2
    order_buy_probability: 1/30
    order_sell_probability: 1/20
    history_buy_probability: 1/30
    history_sell_probability: 1/20
  #- [here, and]
  #- {it: updates, in: real-time}"""


@dataclass
class ResellResume:
    timestamp: datetime
    buy_order: float
    sell_order: float
    sell_order_no_fee: float
    profit: float
    sells_history: dict[str, (int, int)]
    buy_orders_before_desired: int
    sell_orders_before_desired: int
    buy_probability: float
    sell_probability: float


async def _create_resume(history: MarketItemSellHistory, result: SellHistoryAnalyzeResult, orders: MarketItemOrders):
    desired_sell_order = result.sell_order
    profit = round(desired_sell_order * 0.05, 2)
    desired_sell_order_no_fee = result.sell_order_no_fee
    desired_buy_order = result.sell_order_no_fee - profit
    buy_orders_before_desired, buy_probability, sell_orders_before_desired, sell_probability = await _compute_buy_sell_probability(
        desired_sell_order, desired_sell_order_no_fee, orders, result)

    sells_history = await _compute_sell_history(desired_sell_order, history.history)

    resume = ResellResume(
        timestamp=orders.timestamp,
        buy_order=desired_buy_order,
        sell_order=desired_sell_order,
        sell_order_no_fee=desired_sell_order_no_fee,
        profit=profit,
        sells_history=sells_history,
        buy_orders_before_desired=buy_orders_before_desired,
        sell_orders_before_desired=sell_orders_before_desired,
        buy_probability=buy_probability,
        sell_probability=sell_probability,
    )
    return resume


async def _compute_buy_sell_probability(desired_sell_order, desired_sell_order_no_fee, orders,
                                        result):
    orders_full: tuple[list[MarketItemOrder], list[MarketItemOrder]] = _parse_orders(
        json.loads(orders.dump))
    buy_orders_before_desired = 0
    sell_orders_before_desired = 0
    for order in orders_full[0]:
        if order.price >= desired_sell_order_no_fee:
            buy_orders_before_desired += order.quantity
    for order in orders_full[1]:
        if order.price < desired_sell_order:
            sell_orders_before_desired += order.quantity
    buy_probability_frac = buy_orders_before_desired / result.sells_last_day if result.sells_last_day else None
    sell_probability_frac = sell_orders_before_desired / result.sells_last_day if result.sells_last_day else None
    buy_probability = 1 / buy_probability_frac if buy_probability_frac else 0
    sell_probability = 1 / sell_probability_frac if sell_probability_frac else 1
    return buy_orders_before_desired, buy_probability, sell_orders_before_desired, sell_probability


async def _compute_sell_history(desired_sell_order, history):
    j = json.loads(history)
    sells_last_day = 0
    sells_last_day_desired = 0
    sells_last_week = 0
    sells_last_week_desired = 0
    sells_last_month = 0
    sells_last_month_desired = 0
    curr_dt = steam_date_str_to_datetime(j[-1][0])
    for timestamp, price, amount in reversed(j):
        dt = steam_date_str_to_datetime(timestamp)
        price = round(price, 2)
        amount = int(amount)
        if curr_dt - dt <= timedelta(days=1):
            sells_last_day += amount
            if price >= desired_sell_order:
                sells_last_day_desired += amount
        if curr_dt - dt <= timedelta(days=7):
            sells_last_week += amount
            if price >= desired_sell_order:
                sells_last_week_desired += amount
        if curr_dt - dt <= timedelta(days=30):
            sells_last_month += amount
            if price >= desired_sell_order:
                sells_last_month_desired += amount
        if curr_dt - dt > timedelta(days=30):
            break
    return {
            "day": {"all": sells_last_day, "desired": sells_last_day_desired},
            "week": {"all": sells_last_week, "desired": sells_last_week_desired},
            "month": {"all": sells_last_month, "desired": sells_last_month_desired},
                       }


class ExportYaml:
    def __init__(
            self,
            unit_of_work: Callable[..., IUnitOfWork],
    ):
        self._uow = unit_of_work

    async def _export(self, app_id: int, currency: int):
        resumes = {}
        async with self._uow() as uow:
            async for results in uow.sell_history_analyze_result.yield_all(
                    app_id=app_id,
                    currency=currency,
                    count=250,
            ):
                for result in results:
                    if result.recommended:
                        orders = await uow.market_item_orders.get(
                            app_id=result.app_id,
                            market_hash_name=result.market_hash_name,
                            currency=currency
                        )
                        history = await uow.sell_history.get(result.app_id, result.market_hash_name, currency)
                        if orders.buy_order and orders.sell_order:
                            resume = await _create_resume(history, result, orders)
                            if resume.buy_probability >= 1 and resume.sell_probability >= 1:
                                resumes[result.market_hash_name] = resume
        pass

    async def export(self, currency: int) -> None:
        await self._export(730, currency)
        # async with self._uow() as uow:
        #     apps = await uow.game.get_all()
        #     for app in apps:

