import functools
import json
import operator
import statistics
from datetime import datetime, timedelta

from steam_trade_bot.domain.entities.market import SellHistoryAnalyzeResult, MarketItemSellHistory
from steam_trade_bot.domain.steam_fee import SteamFee

_MAX_FALL_DEVIATION = 0.05
_MEAN_MAX_THRESHOLD = 0.1
_MEAN_MIN_THRESHOLD = 0.1
_WINDOWS_SIZE = 15
_MAX_DEVIATION = 0.06
_MIN_SELLS_PER_WEEK = 10
_QUANTILES_MIN_POINTS = 10


def steam_date_str_to_datetime(s: str) -> datetime:
    """
    converts str like 'Mar 16 2017 01: +0' to datetime:
    """
    s = s[: s.index(":")]
    return datetime.strptime(s, "%b %d %Y %H")


def percentage_diff(price1: float, price2: float) -> float:
    min_ = min(price1, price2)
    max_ = max(price1, price2)
    return (max_ - min_) / max_


def window_slicing(k, iter_):
    for i in range(0, len(iter_) - k + 1):
        yield iter_[i : i + k]


class SellHistoryAnalyzer:
    async def analyze(self, history: MarketItemSellHistory) -> SellHistoryAnalyzeResult:
        j = json.loads(history.history)

        sells_last_day = 0
        sells_last_week = 0
        sells_last_month = 0

        curr_dt = datetime.now()
        to_process = []
        for timestamp, price, amount in reversed(j):
            dt = steam_date_str_to_datetime(timestamp)
            price = round(price, 2)
            amount = int(amount)
            if curr_dt - dt <= timedelta(days=1):
                sells_last_day += amount
            if curr_dt - dt <= timedelta(days=7):
                sells_last_week += amount
            if curr_dt - dt <= timedelta(days=30):
                sells_last_month += amount
            if curr_dt - dt > timedelta(days=30):
                break
            else:
                to_process.append((dt, price, amount))

        if len(to_process) < _QUANTILES_MIN_POINTS:
            return SellHistoryAnalyzeResult(
                app_id=history.app_id,
                market_hash_name=history.market_hash_name,
                timestamp=history.timestamp,
                sells_last_day=sells_last_day,
                sells_last_week=sells_last_week,
                sells_last_month=sells_last_month,
                recommended=False,
                deviation=None,
                sell_order=None,
                sell_order_no_fee=None,
            )

        to_process = list(reversed(to_process))

        prices = [x[1] for x in to_process]
        # dispersion = statistics.pvariance(prices)
        quantiles_count = 10
        quantiles = statistics.quantiles(prices, n=quantiles_count)
        # windows = list(window_slicing(50, prices))
        # percentile_20 = quantiles[1]  # 1 is 20% percentile
        percentile_80 = quantiles[7]  # 7 is 80% percentile
        sell_order = round(percentile_80, 2)

        slices = window_slicing(_WINDOWS_SIZE, to_process)
        slices = tuple(slices)
        slices_mean_prices = tuple(
            statistics.harmonic_mean(
                data=map(operator.itemgetter(1), slice_),  # price
                weights=map(operator.itemgetter(2), slice_),  # sold amount
            )
            for slice_ in slices
        )
        slices_mean_prices = map(functools.partial(round, ndigits=2), slices_mean_prices)
        slices_mean_prices = tuple(slices_mean_prices)
        if len(slices_mean_prices) < 5:
            return SellHistoryAnalyzeResult(
                app_id=history.app_id,
                market_hash_name=history.market_hash_name,
                timestamp=history.timestamp,
                sells_last_day=sells_last_day,
                sells_last_week=sells_last_week,
                sells_last_month=sells_last_month,
                recommended=False,
                deviation=None,
                sell_order=sell_order,
                sell_order_no_fee=SteamFee.subtract_fee(sell_order),
            )
        mean_min = min(slices_mean_prices)
        mean_max = max(slices_mean_prices)
        med = statistics.median(slices_mean_prices)
        perc_diff_min = percentage_diff(mean_min, med)
        perc_diff_max = percentage_diff(mean_max, med)
        deviation = statistics.stdev(slices_mean_prices) / med
        fall_deviation = statistics.stdev([slices_mean_prices[0], slices_mean_prices[-1]]) / med
        is_fall_ok = fall_deviation < _MAX_FALL_DEVIATION
        is_low_deviation = deviation < _MAX_DEVIATION
        is_min_ok = perc_diff_min < _MEAN_MIN_THRESHOLD
        is_max_ok = perc_diff_max < _MEAN_MAX_THRESHOLD
        is_ok = is_min_ok and is_max_ok
        recommended = (
            is_fall_ok and is_low_deviation and is_ok and (sells_last_week >= _MIN_SELLS_PER_WEEK)
        )

        return SellHistoryAnalyzeResult(
            app_id=history.app_id,
            market_hash_name=history.market_hash_name,
            timestamp=history.timestamp,
            sells_last_day=sells_last_day,
            sells_last_week=sells_last_week,
            sells_last_month=sells_last_month,
            recommended=recommended,
            deviation=deviation,
            sell_order=sell_order,
            sell_order_no_fee=SteamFee.subtract_fee(sell_order),
        )
