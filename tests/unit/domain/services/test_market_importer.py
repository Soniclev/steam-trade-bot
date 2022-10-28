import json

import pytest

from steam_trade_bot.domain.entities.market import MarketItemOrder
from steam_trade_bot.domain.services.market_item_importer import _parse_orders


@pytest.fixture
def orders_histogram():
    with open("tests/unit/domain/services/data/orders_histogram.json", "r") as f:
        return json.loads(f.read())


def test__parse_orders__buy_orders(orders_histogram):
    buy_orders, _ = _parse_orders(orders_histogram)

    assert buy_orders[0] == MarketItemOrder(
        price=0.13,
        quantity=95,
    )

    assert buy_orders[-1] == MarketItemOrder(
        price=0.03,
        quantity=106,
    )
    assert len(buy_orders) == 10


def test__parse_orders__sell_orders(orders_histogram):
    _, sell_orders = _parse_orders(orders_histogram)

    assert sell_orders[0] == MarketItemOrder(
        price=0.14,
        quantity=1,
    )
    assert sell_orders[-1] == MarketItemOrder(
        price=0.27,
        quantity=1,
    )
    assert len(sell_orders) == 11
