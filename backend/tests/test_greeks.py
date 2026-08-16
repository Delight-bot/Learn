import pytest

from quant.black_scholes import OptionParams, black_scholes_price
from quant.greeks import compute_greeks

BASE = dict(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20)


def _price(option_type, **overrides):
    params = {**BASE, **overrides}
    return black_scholes_price(OptionParams(option_type=option_type, **params))


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_delta_matches_finite_difference(option_type):
    h = 0.01
    fd_delta = (_price(option_type, S=BASE["S"] + h) - _price(option_type, S=BASE["S"] - h)) / (2 * h)
    greeks = compute_greeks(OptionParams(option_type=option_type, **BASE))
    assert greeks.delta == pytest.approx(fd_delta, abs=1e-3)


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_gamma_matches_finite_difference(option_type):
    h = 0.5
    fd_gamma = (
        _price(option_type, S=BASE["S"] + h) - 2 * _price(option_type, S=BASE["S"]) + _price(option_type, S=BASE["S"] - h)
    ) / (h ** 2)
    greeks = compute_greeks(OptionParams(option_type=option_type, **BASE))
    assert greeks.gamma == pytest.approx(fd_gamma, abs=1e-3)


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_vega_matches_finite_difference(option_type):
    # Our vega is per 1% (0.01) change in sigma, so bump sigma by a small
    # absolute amount and scale the finite-difference derivative accordingly.
    h = 0.0001
    dprice_dsigma = (_price(option_type, sigma=BASE["sigma"] + h) - _price(option_type, sigma=BASE["sigma"] - h)) / (2 * h)
    fd_vega_per_percent = dprice_dsigma * 0.01
    greeks = compute_greeks(OptionParams(option_type=option_type, **BASE))
    assert greeks.vega == pytest.approx(fd_vega_per_percent, abs=1e-3)


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_theta_matches_finite_difference(option_type):
    # Our theta is per calendar day (time decay), so bump T by a small
    # fraction of a day and negate (theta = -dV/dT), scaled to 1 day.
    h = 1e-5
    dprice_dT = (_price(option_type, T=BASE["T"] + h) - _price(option_type, T=BASE["T"] - h)) / (2 * h)
    fd_theta_per_day = -dprice_dT / 365.0
    greeks = compute_greeks(OptionParams(option_type=option_type, **BASE))
    assert greeks.theta == pytest.approx(fd_theta_per_day, abs=1e-3)


def test_call_delta_between_zero_and_one():
    greeks = compute_greeks(OptionParams(option_type="call", **BASE))
    assert 0.0 <= greeks.delta <= 1.0


def test_put_delta_between_minus_one_and_zero():
    greeks = compute_greeks(OptionParams(option_type="put", **BASE))
    assert -1.0 <= greeks.delta <= 0.0


def test_gamma_is_identical_for_call_and_put():
    call_greeks = compute_greeks(OptionParams(option_type="call", **BASE))
    put_greeks = compute_greeks(OptionParams(option_type="put", **BASE))
    assert call_greeks.gamma == pytest.approx(put_greeks.gamma, abs=1e-10)


def test_vega_is_identical_for_call_and_put():
    call_greeks = compute_greeks(OptionParams(option_type="call", **BASE))
    put_greeks = compute_greeks(OptionParams(option_type="put", **BASE))
    assert call_greeks.vega == pytest.approx(put_greeks.vega, abs=1e-10)


def test_greeks_at_expiration_are_flat():
    call_greeks = compute_greeks(OptionParams(S=110, K=100, T=0, r=0.05, sigma=0.2, option_type="call"))
    assert call_greeks.gamma == 0.0
    assert call_greeks.vega == 0.0
    assert call_greeks.theta == 0.0
    assert call_greeks.delta == 1.0

    otm_call_greeks = compute_greeks(OptionParams(S=90, K=100, T=0, r=0.05, sigma=0.2, option_type="call"))
    assert otm_call_greeks.delta == 0.0
