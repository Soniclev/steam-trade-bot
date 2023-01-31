import pytest

from steam_trade_bot.domain.fee_calculator import compute_fee_from_payload, compute_fee_from_total


@pytest.mark.parametrize(
    "received, total",
    [
        (0.01, 0.03),
        (0.09, 0.11),
        (0.18, 0.2),
        (0.19, 0.21),
        (0.2, 0.23),
        (0.59, 0.66),
        (0.6, 0.69),
        (1.3, 1.49),
        (2, 2.3),
        (3, 3.45),
        (4, 4.60),
        (5, 5.75),
        (12.43, 14.29),
        (129.43, 148.84),
    ],
)
def test_csgo(received, total):
    fee = compute_fee_from_payload(received)
    backward_fee = compute_fee_from_total(total)

    assert fee.total == total
    assert backward_fee.payload == received


@pytest.mark.parametrize(
    "received, game_fee, total",
    [
        (0.48, 0.07, 0.57),
        (0.56, 0.08, 0.66),
        (0.92, 0.13, 1.09),
    ],
)
def test_app_321360(received, game_fee, total):
    fee = compute_fee_from_payload(received, game=0.15)
    backward_fee = compute_fee_from_total(total, game=0.15)

    assert fee.total == total
    assert fee.game == game_fee
    assert backward_fee.payload == received
    assert backward_fee.game == game_fee


@pytest.mark.parametrize(
    "game_fee",
    [
        None,
        0.10,
        0.15,
    ],
)
def test_fee_from_1_cent_to_2000_bucks(game_fee):
    # test all prices from $0.01 to $2000
    prev_price = None
    for i in range(1, 2000_01):
        price = round(i / 100, 2)
        price_with_fee = compute_fee_from_payload(price, game=game_fee)
        backward_fee = compute_fee_from_total(price_with_fee.total, game=game_fee)
        assert backward_fee.game >= 0.01
        assert backward_fee.steam >= 0.01
        assert backward_fee.total == round(backward_fee.payload + backward_fee.steam + backward_fee.game, 2)
        assert backward_fee.payload == price
        # need to check corner cases, like:
        # 0.19 -> 0.21
        # 0.19 -> 0.22
        if prev_price:
            while price - 0.01 > prev_price:
                prev_price = round(prev_price + 0.01, 2)
                price_with_fee = compute_fee_from_payload(prev_price, game=game_fee)
                backward_fee = compute_fee_from_total(price_with_fee.total, game=game_fee)
                assert backward_fee.game >= 0.01
                assert backward_fee.steam >= 0.01
                assert backward_fee.total == round(backward_fee.payload + backward_fee.steam + backward_fee.game, 2)
                assert backward_fee.payload == price
        prev_price = price
