from operator import itemgetter

ORDERS_PAIR = tuple[float, int]


def parse_orders(data: dict) -> tuple[list[ORDERS_PAIR], list[ORDERS_PAIR]]:
    def _load_from_graph(graph, orders):
        last_quantity = 0
        for price, quantity, _ in graph:
            if price not in orders:
                orders[price] = (price, int(quantity - last_quantity))
            last_quantity = quantity

    buy_orders = {}
    sell_orders = {}
    _load_from_graph(data["buy_order_graph"], buy_orders)
    _load_from_graph(data["sell_order_graph"], sell_orders)

    return sorted(buy_orders.values(), key=itemgetter(0), reverse=True), sorted(
        sell_orders.values(), key=itemgetter(0), reverse=False
    )
