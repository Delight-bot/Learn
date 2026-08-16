"""
Monte Carlo European option pricing under risk-neutral geometric Brownian
motion, implemented from scratch with NumPy.

Terminal stock price under the risk-neutral measure:

    S_T = S_0 * exp((r - 0.5 * sigma^2) * T + sigma * sqrt(T) * Z),  Z ~ N(0, 1)

Payoff:
    call: max(S_T - K, 0)
    put:  max(K - S_T, 0)

The option price is the discounted expected payoff:

    price = exp(-r * T) * E[payoff]

The standard error of that Monte Carlo estimate is:

    SE = exp(-r * T) * std(payoff) / sqrt(n_simulations)
"""

from dataclasses import dataclass

import numpy as np

from .black_scholes import OptionParams


@dataclass(frozen=True)
class MonteCarloResult:
    price: float
    std_error: float
    n_simulations: int
    terminal_prices: np.ndarray  # full array, for convergence/summary use
    sample_paths: np.ndarray     # (n_paths_to_plot, n_steps+1) price paths


def _terminal_prices(params: OptionParams, n_simulations: int, rng: np.random.Generator) -> np.ndarray:
    S, T, r, sigma = params.S, params.T, params.r, params.sigma
    Z = rng.standard_normal(n_simulations)
    return S * np.exp((r - 0.5 * sigma ** 2) * T + sigma * np.sqrt(T) * Z)


def _payoff(params: OptionParams, terminal_prices: np.ndarray) -> np.ndarray:
    if params.option_type == "call":
        return np.maximum(terminal_prices - params.K, 0.0)
    return np.maximum(params.K - terminal_prices, 0.0)


def simulate_price_paths(
    params: OptionParams,
    n_paths: int = 60,
    n_steps: int = 100,
    seed: int | None = None,
) -> np.ndarray:
    """Simulate full price paths (not just terminal prices) for plotting.

    Uses the same risk-neutral GBM dynamics, discretized into n_steps
    equal time increments via Euler-Maruyama on log-price (exact for GBM).
    """
    S, T, r, sigma = params.S, params.T, params.r, params.sigma
    rng = np.random.default_rng(seed)

    dt = T / n_steps if n_steps > 0 else 0.0
    Z = rng.standard_normal((n_paths, n_steps))
    log_increments = (r - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * Z
    log_paths = np.cumsum(log_increments, axis=1)
    paths = S * np.exp(np.concatenate([np.zeros((n_paths, 1)), log_paths], axis=1))
    return paths


def monte_carlo_price(
    params: OptionParams,
    n_simulations: int = 10_000,
    n_plot_paths: int = 60,
    n_plot_steps: int = 100,
    seed: int | None = None,
) -> MonteCarloResult:
    """Price a European option via Monte Carlo simulation.

    Returns the discounted price, its standard error, and a small sample
    of full price paths suitable for plotting (kept separate from the
    n_simulations terminal draws used for the pricing estimate itself,
    since we should not plot all 100,000 paths).
    """
    rng = np.random.default_rng(seed)

    if params.T <= 0:
        intrinsic = max(params.S - params.K, 0.0) if params.option_type == "call" else max(params.K - params.S, 0.0)
        flat_path = np.full((min(n_plot_paths, 10), n_plot_steps + 1), params.S)
        return MonteCarloResult(
            price=intrinsic,
            std_error=0.0,
            n_simulations=n_simulations,
            terminal_prices=np.full(n_simulations, params.S),
            sample_paths=flat_path,
        )

    terminal_prices = _terminal_prices(params, n_simulations, rng)
    payoffs = _payoff(params, terminal_prices)
    discount = np.exp(-params.r * params.T)

    price = discount * float(np.mean(payoffs))
    std_error = discount * float(np.std(payoffs, ddof=1) / np.sqrt(n_simulations)) if n_simulations > 1 else 0.0

    sample_paths = simulate_price_paths(params, n_paths=n_plot_paths, n_steps=n_plot_steps, seed=seed)

    return MonteCarloResult(
        price=price,
        std_error=std_error,
        n_simulations=n_simulations,
        terminal_prices=terminal_prices,
        sample_paths=sample_paths,
    )


def convergence_series(
    params: OptionParams,
    simulation_counts: list[int],
    seed: int | None = None,
) -> list[dict]:
    """Compute the Monte Carlo price at each simulation count in
    simulation_counts, reusing one large draw of standard normals so
    the series is a genuine convergence path (each larger estimate
    includes the smaller one's draws) rather than independent re-runs.
    """
    rng = np.random.default_rng(seed)
    max_n = max(simulation_counts)
    Z = rng.standard_normal(max_n)

    S, T, r, sigma = params.S, params.T, params.r, params.sigma
    terminal_prices = S * np.exp((r - 0.5 * sigma ** 2) * T + sigma * np.sqrt(T) * Z)
    payoffs = _payoff(params, terminal_prices)
    discount = np.exp(-r * T)

    results = []
    for n in sorted(simulation_counts):
        cum_mean = float(np.mean(payoffs[:n]))
        results.append({"n_simulations": n, "price": discount * cum_mean})
    return results
