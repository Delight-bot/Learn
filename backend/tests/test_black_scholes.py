import math

import pytest

from quant.black_scholes import OptionParams, black_scholes_price, call_price, put_price


def test_call_price_matches_known_reference():
    # S=100, K=100, T=1y, r=5%, sigma=20% -> textbook reference ~10.4506
    price = call_price(S=100, K=100, T=1, r=0.05, sigma=0.20)
    assert price == pytest.approx(10.4506, abs=1e-3)


def test_put_price_matches_known_reference():
    # Same scenario -> textbook reference ~5.5735
    price = put_price(S=100, K=100, T=1, r=0.05, sigma=0.20)
    assert price == pytest.approx(5.5735, abs=1e-3)


def test_second_reference_case():
    # S=50, K=45, T=0.5y, r=3%, sigma=25% -> call ~6.66, put ~1.00 (standard textbook case)
    call = call_price(S=50, K=45, T=0.5, r=0.03, sigma=0.25)
    put = put_price(S=50, K=45, T=0.5, r=0.03, sigma=0.25)
    assert call == pytest.approx(6.8954, abs=1e-3)
    assert put == pytest.approx(1.2255, abs=1e-3)


@pytest.mark.parametrize("S,K,T,r,sigma", [
    (450, 460, 30 / 365, 0.045, 0.20),
    (100, 80, 2.0, 0.02, 0.35),
    (30, 30, 0.25, 0.01, 0.10),
])
def test_put_call_parity(S, K, T, r, sigma):
    # C - P = S - K * exp(-rT)
    C = call_price(S, K, T, r, sigma)
    P = put_price(S, K, T, r, sigma)
    lhs = C - P
    rhs = S - K * math.exp(-r * T)
    assert lhs == pytest.approx(rhs, abs=1e-8)


def test_deep_in_the_money_call_approaches_intrinsic():
    price = call_price(S=1000, K=100, T=1, r=0.05, sigma=0.20)
    intrinsic = 1000 - 100 * math.exp(-0.05)
    assert price == pytest.approx(intrinsic, abs=0.5)


def test_deep_out_of_the_money_call_approaches_zero():
    price = call_price(S=10, K=1000, T=0.5, r=0.05, sigma=0.20)
    assert price < 1e-6


def test_zero_time_to_expiration_returns_intrinsic_value():
    call = black_scholes_price(OptionParams(S=110, K=100, T=0, r=0.05, sigma=0.2, option_type="call"))
    put = black_scholes_price(OptionParams(S=90, K=100, T=0, r=0.05, sigma=0.2, option_type="put"))
    assert call == pytest.approx(10.0)
    assert put == pytest.approx(10.0)


def test_near_zero_time_to_expiration_is_close_to_intrinsic():
    call = call_price(S=110, K=100, T=1e-6, r=0.05, sigma=0.2)
    assert call == pytest.approx(10.0, abs=0.05)


def test_very_low_volatility_behaves_like_forward_intrinsic():
    # With near-zero vol, the call is worth ~ discounted intrinsic of the forward price.
    S, K, T, r, sigma = 100, 90, 1.0, 0.05, 1e-6
    price = call_price(S, K, T, r, sigma)
    forward = S * math.exp(r * T)
    expected = math.exp(-r * T) * max(forward - K, 0.0)
    assert price == pytest.approx(expected, abs=1e-3)


def test_invalid_option_type_raises():
    with pytest.raises(ValueError):
        OptionParams(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type="straddle")


def test_negative_price_or_strike_raises():
    with pytest.raises(ValueError):
        OptionParams(S=-1, K=100, T=1, r=0.05, sigma=0.2, option_type="call")
