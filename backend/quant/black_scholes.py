"""
Black-Scholes European option pricing, implemented from scratch.

The Black-Scholes model prices a European option under the assumptions of
a lognormal stock price process, constant volatility, constant risk-free
rate, and no dividends or transaction costs.

Notation:
    S     - current stock price
    K     - strike price
    T     - time to expiration, in years
    r     - risk-free interest rate (annualized, continuously compounded)
    sigma - annualized volatility of the underlying's returns

d1 and d2 are defined as:

    d1 = [ln(S / K) + (r + sigma^2 / 2) * T] / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

Call price:
    C = S * N(d1) - K * exp(-r * T) * N(d2)

Put price (via put-call parity):
    P = K * exp(-r * T) * N(-d2) - S * N(-d1)

where N(.) is the standard normal cumulative distribution function.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class OptionParams:
    S: float      # current stock price
    K: float      # strike price
    T: float      # time to expiration in years
    r: float      # risk-free rate (annualized, decimal e.g. 0.045)
    sigma: float  # volatility (annualized, decimal e.g. 0.20)
    option_type: str  # "call" or "put"

    def __post_init__(self):
        if self.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'")
        if self.S <= 0 or self.K <= 0:
            raise ValueError("S and K must be positive")
        if self.T < 0:
            raise ValueError("T must be non-negative")
        if self.sigma < 0:
            raise ValueError("sigma must be non-negative")


def norm_cdf(x: float) -> float:
    """Standard normal CDF via the error function (no external deps)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def d1_d2(S: float, K: float, T: float, r: float, sigma: float) -> tuple[float, float]:
    """Compute d1 and d2 for the Black-Scholes formula.

    Handles the T -> 0 or sigma -> 0 edge case (no time value / no
    randomness left) by returning +/- infinity so downstream N(d1)/N(d2)
    collapse to the correct intrinsic-value limits.
    """
    if T <= 0 or sigma <= 0:
        # No time value or no volatility: d1, d2 -> +/-inf depending on moneyness.
        intrinsic_sign = 1.0 if S > K else (-1.0 if S < K else 0.0)
        d = math.inf * intrinsic_sign if intrinsic_sign != 0 else 0.0
        return d, d

    sqrt_T = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    return d1, d2


def black_scholes_price(params: OptionParams) -> float:
    """Theoretical European option price under Black-Scholes."""
    S, K, T, r, sigma = params.S, params.K, params.T, params.r, params.sigma

    if T <= 0:
        # At expiration the option is worth its intrinsic value.
        if params.option_type == "call":
            return max(S - K, 0.0)
        return max(K - S, 0.0)

    d1, d2 = d1_d2(S, K, T, r, sigma)

    if params.option_type == "call":
        return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    return K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)


def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return black_scholes_price(OptionParams(S, K, T, r, sigma, "call"))


def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return black_scholes_price(OptionParams(S, K, T, r, sigma, "put"))
