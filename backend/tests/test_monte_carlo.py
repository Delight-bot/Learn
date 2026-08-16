import pytest

from quant.black_scholes import OptionParams, black_scholes_price
from quant.monte_carlo import monte_carlo_price, convergence_series, simulate_price_paths

BASE = dict(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20)


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_monte_carlo_converges_to_black_scholes(option_type):
    params = OptionParams(option_type=option_type, **BASE)
    bs_price = black_scholes_price(params)
    mc_result = monte_carlo_price(params, n_simulations=200_000, seed=42)

    # Should be within ~4 standard errors of the analytical price.
    assert abs(mc_result.price - bs_price) <= 4 * mc_result.std_error


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_monte_carlo_error_shrinks_with_more_simulations(option_type):
    params = OptionParams(option_type=option_type, **BASE)
    small = monte_carlo_price(params, n_simulations=1_000, seed=1)
    large = monte_carlo_price(params, n_simulations=100_000, seed=1)
    assert large.std_error < small.std_error


def test_monte_carlo_is_reproducible_with_fixed_seed():
    params = OptionParams(option_type="call", **BASE)
    a = monte_carlo_price(params, n_simulations=5_000, seed=123)
    b = monte_carlo_price(params, n_simulations=5_000, seed=123)
    assert a.price == b.price
    assert a.std_error == b.std_error


def test_convergence_series_approaches_black_scholes_price():
    params = OptionParams(option_type="call", **BASE)
    bs_price = black_scholes_price(params)
    series = convergence_series(params, [100, 1_000, 10_000, 100_000], seed=7)

    errors = [abs(point["price"] - bs_price) for point in series]
    # The error at 100,000 simulations should generally be smaller than at 100.
    assert errors[-1] < errors[0]


def test_sample_paths_shape_and_start_at_spot_price():
    params = OptionParams(option_type="call", **BASE)
    paths = simulate_price_paths(params, n_paths=25, n_steps=50, seed=0)
    assert paths.shape == (25, 51)
    assert (paths[:, 0] == params.S).all()


def test_monte_carlo_zero_time_returns_intrinsic_value():
    params = OptionParams(S=110, K=100, T=0, r=0.05, sigma=0.2, option_type="call")
    result = monte_carlo_price(params, n_simulations=1_000, seed=0)
    assert result.price == pytest.approx(10.0)
    assert result.std_error == 0.0


def test_monte_carlo_deep_out_of_the_money_prices_near_zero():
    params = OptionParams(S=10, K=1000, T=0.5, r=0.05, sigma=0.2, option_type="call")
    result = monte_carlo_price(params, n_simulations=50_000, seed=0)
    assert result.price < 0.01
