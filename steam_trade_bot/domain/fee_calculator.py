from typing import NamedTuple

ComputedFee = NamedTuple("ComputedFee", total=float, payload=float, game=float, steam=float)


def compute_fee_from_payload(payload: float, game: float | None = None) -> ComputedFee:
    pass


def compute_fee_from_total(total, game: float | None = None) -> ComputedFee:
    pass


