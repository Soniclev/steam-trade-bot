import math
from typing import NamedTuple

ComputedFee = NamedTuple(
    "ComputedFee",
    [("total", float), ("payload", float), ("game", float), ("steam", float)]
)

WALLET_FEE_MINIMUM = 0.01
WALLET_FEE_PERCENT = 0.05
WALLET_FEE_BASE = 0


def compute_fee_from_payload(payload: float, game: float | None = None) -> ComputedFee:
    steam_fee = math.floor(max(payload * WALLET_FEE_PERCENT, WALLET_FEE_MINIMUM) * 100) / 100
    game_fee = math.floor(max(payload * (game or 0.1), WALLET_FEE_MINIMUM) * 100) / 100
    total_fee = WALLET_FEE_BASE + game_fee + steam_fee
    total = round(payload + total_fee, 2)
    return ComputedFee(total=total, payload=payload, game=game_fee, steam=steam_fee)


def compute_fee_from_total(total: float, game: float | None = None) -> ComputedFee:
    start_payload = round(total * 0.9, 2)
    for _ in range(100):
        fee = compute_fee_from_payload(start_payload, game)
        diff = total - fee.total
        if fee.total == total:
            return fee
        elif fee.total > total:
            start_payload = round(start_payload - max(total * 0.01, 0.01), 2)
        else:
            start_payload = round(start_payload + max(diff * 0.4, 0.01), 2)

    raise ValueError("Failed to compute fee in 100 cycles")
