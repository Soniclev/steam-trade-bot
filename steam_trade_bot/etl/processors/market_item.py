import functools
import json

from steam_trade_bot.domain.fee_calculator import ComputedFee, compute_fee_from_total
from steam_trade_bot.domain.services.orders_parser import parse_orders
from steam_trade_bot.domain.services.sell_history_analyzer import steam_date_str_to_datetime
from steam_trade_bot.etl.models import MarketItemRaw, MarketItemStage, MarketItemDWH, \
    MarketItemSellHistoryRaw, MarketItemSellHistoryStage, MarketItemSellHistoryDWH, \
    MarketItemStatsStage, MarketItemStatsDWH, MarketItemOrdersRaw, MarketItemOrdersStage, \
    MarketItemOrdersDWH


@functools.lru_cache(typed=False)
def _cached_compute_fee_from_total(total: float, game: float | None = None) -> ComputedFee:
    return compute_fee_from_total(total=total, game=game)


def extract_sell_history_stats_from_row(row):
    # print(row["app_id"], row["market_hash_name"])
    history = json.loads(row["history"])
    points = []
    for item in history:
        timestamp = steam_date_str_to_datetime(item[0])
        price = round(item[1], 2)
        amount = int(item[2])
        points.append((timestamp, price, amount))
    total_sold = sum(x[2] for x in points)
    total_volume = round(sum(x[1] * x[2] for x in points), 2)
    total_volume_steam_fee = round(
        sum(_cached_compute_fee_from_total(x[1]).steam * x[2] for x in points),
        2)
    total_volume_publisher_fee = round(
        sum(_cached_compute_fee_from_total(x[1]).game * x[2] for x in points),
        2)
    first_sale_timestamp = points[0][0] if points else None
    last_sale_timestamp = points[-1][0] if points else None
    prices = [p[1] for p in points]
    max_price = max(prices) if prices else None
    min_price = min(prices) if prices else None

    return {
        "app_id": row["app_id"],
        "market_hash_name": row["market_hash_name"],
        "total_sold": total_sold,
        "total_volume": total_volume,
        "total_volume_steam_fee": total_volume_steam_fee,
        "total_volume_publisher_fee": total_volume_publisher_fee,
        "first_sale_timestamp": first_sale_timestamp,
        "last_sale_timestamp": last_sale_timestamp,
        "max_price": max_price,
        "min_price": min_price,
    }


def extract_sell_history_from_row(row):
    # print(row["app_id"], row["market_hash_name"])
    history = json.loads(row["history"])
    points = []
    for item in history:
        timestamp = steam_date_str_to_datetime(item[0]).timestamp()
        price = round(item[1], 2)
        amount = int(item[2])
        points.append((timestamp, price, amount))

    json_history = json.dumps(points)

    return {
        "app_id": row["app_id"],
        "market_hash_name": row["market_hash_name"],
        "timestamp": row["timestamp"],
        "history": json_history,
    }


def extract_orders_from_row(row):
    # print(row.app_id, row.market_hash_name)
    buy_orders, sell_orders = parse_orders(json.loads(row["dump"]))

    return {
        "app_id": row["app_id"],
        "market_hash_name": row["market_hash_name"],
        "timestamp": row["timestamp"],
        "buy_orders": json.dumps(buy_orders),
        "sell_orders": json.dumps(sell_orders),
    }


def process_market_item(
        obj: MarketItemRaw
) -> tuple[MarketItemStage, MarketItemDWH]:
    dict_ = dict(**obj)
    if dict_["market_fee"]:
        dict_["market_fee"] = round(float(dict_["market_fee"]), 2)
    else:
        dict_["market_fee"] = None
    return (
        MarketItemStage(**dict_),
        MarketItemDWH(**dict_)
    )


def process_market_item_sell_history(
        obj: MarketItemSellHistoryRaw
) -> tuple[
    MarketItemSellHistoryStage, MarketItemSellHistoryDWH, MarketItemStatsStage, MarketItemStatsDWH]:
    processed_sell_history = extract_sell_history_from_row(obj)
    processed_stats = extract_sell_history_stats_from_row(obj)
    return (
        MarketItemSellHistoryStage(**processed_sell_history),
        MarketItemSellHistoryDWH(**processed_sell_history),
        MarketItemStatsStage(**processed_stats),
        MarketItemStatsDWH(**processed_stats),
    )


def process_market_item_orders(
        obj: MarketItemOrdersRaw
) -> tuple[MarketItemOrdersStage, MarketItemOrdersDWH]:
    processed = extract_orders_from_row(obj)
    return (
        MarketItemOrdersStage(**processed),
        MarketItemOrdersDWH(**processed),
    )
