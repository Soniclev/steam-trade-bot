import math
from typing import NamedTuple

ComputedFee = NamedTuple(
    "ComputedFee",
    [("total", float), ("payload", float), ("game", float), ("steam", float)]
)

WALLET_FEE_MINIMUM = 0.01
WALLET_FEE_PERCENT = 0.05
WALLET_FEE_BASE = 0
DEFAULT_PUBLISHER_FEE = 0.1


def compute_fee_from_payload(payload: float, game: float | None = None) -> ComputedFee:
    """
    Computes in O(1) the total cost, game fee, steam fee, and payload given the payload and game fee.
    If no game fee is provided, it defaults to 0.1.

    Example usage:

    >>> compute_fee_from_payload(10.0)
    ComputedFee(total=11.5, payload=10.0, game=1.0, steam=0.5)

    >>> compute_fee_from_payload(10.0, 0.2)
    ComputedFee(total=12.0, payload=10.0, game=2.0, steam=0.5)

    :param payload: Price that user expect to receive
    :param game: Game fee in range 0-1. By default, it's 0.1
    :return: A named tuple with fields ('total', 'payload', 'game', 'steam')
    """
    if payload < 0.01:
        raise ValueError("Payload value must be greater than 0.01")
    if game and (game < 0 or game > 1):
        raise ValueError("Game fee value is exceed [0;1] range")
    payload = round(payload, 2)
    steam_fee = math.floor(payload * WALLET_FEE_PERCENT * 100) / 100
    game_fee = math.floor(payload * (game or DEFAULT_PUBLISHER_FEE) * 100) / 100
    steam_fee, game_fee = max(steam_fee, WALLET_FEE_MINIMUM), max(game_fee, WALLET_FEE_MINIMUM)
    total_fee = WALLET_FEE_BASE + game_fee + steam_fee
    total = round(payload + total_fee, 2)
    return ComputedFee(total=total, payload=payload, game=game_fee, steam=steam_fee)


def compute_fee_from_total(total: float, game: float | None = None) -> ComputedFee:
    """
    Computes in O(n) the total cost, game fee, steam fee, and payload given the total cost and game fee.
    If no game fee is provided, it defaults to 0.1.

    Example usage:

    >>> compute_fee_from_total(11.5)
    ComputedFee(total=11.5, payload=10.0, game=1.0, steam=0.5)

    >>> compute_fee_from_total(12.0, 0.2)
    ComputedFee(total=12.0, payload=10.0, game=2.0, steam=0.5)

    :param total: Total price which includes payload, steam fee, and game fee.
    :param game: Game fee in range 0-1. By default, it's 0.1
    :return: A named tuple with fields ('total', 'payload', 'game', 'steam')
    """
    if total < 0.03:
        raise ValueError("Total value must be greater than 0.03")
    if game and (game < 0 or game > 1):
        raise ValueError("Game fee value is exceed [0;1] range")
    total = round(total, 2)
    est_payload = round(total / 1.15, 2)
    _map = {}
    for _ in range(100):
        fee = compute_fee_from_payload(est_payload, game)
        _map[fee.payload] = fee.total
        if fee.payload in _map and round(fee.payload+0.01, 2) in _map:
            if _map[fee.payload] < total < _map[round(fee.payload+0.01, 2)]:
                return fee
        if fee.total == total:
            return fee
        elif fee.total > total:
            est_payload = round(est_payload - max(total * 0.01, 0.01), 2)
        else:
            diff = total - fee.total
            est_payload = round(est_payload + max(diff * 0.4, 0.01), 2)

    raise ValueError("Unable to compute fee with the provided parameters. Please check that the inputs are valid and try again.")
