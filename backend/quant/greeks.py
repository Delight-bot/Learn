"""
Black-Scholes Greeks, derived analytically from the pricing formula.

All Greeks are computed directly from d1/d2 rather than via finite
differences, so they are exact under the Black-Scholes assumptions
(finite-difference approximations are only used in tests, to check
these closed-form results independently).

Definitions (S, K, T, r, sigma as in black_scholes.py):

    Delta = dV/dS
        call: N(d1)
        put:  N(d1) - 1

    Gamma = d^2V/dS^2 = N'(d1) / (S * sigma * sqrt(T))
        (identical for calls and puts)

    Vega = dV/dsigma = S * N'(d1) * sqrt(T)
        Reported per 1 percentage-point (1%) change in volatility,
        i.e. divided by 100, since that is the more intuitive unit
        for a beginner-facing UI.

    Theta = dV/dt (time decay, expressed per calendar day)
        call: [-S * N'(d1) * sigma / (2*sqrt(T)) - r*K*exp(-rT)*N(d2)] / 365
        put:  [-S * N'(d1) * sigma / (2*sqrt(T)) + r*K*exp(-rT)*N(-d2)] / 365

Where N(.) is the standard normal CDF and N'(.) is the standard normal PDF.
"""

import math
from dataclasses import dataclass

from .black_scholes import OptionParams, d1_d2, norm_cdf, norm_pdf


@dataclass(frozen=True)
class Greeks:
    delta: float
    gamma: float
    vega: float   # per 1% change in volatility
    theta: float  # per calendar day


def compute_greeks(params: OptionParams) -> Greeks:
    S, K, T, r, sigma = params.S, params.K, params.T, params.r, params.sigma

    if T <= 0 or sigma <= 0:
        # At/after expiration (or with zero volatility) the option's value
        # is piecewise-linear intrinsic value: Delta is 0 or +/-1, and all
        # higher-order sensitivities vanish.
        if params.option_type == "call":
            delta = 1.0 if S > K else 0.0
        else:
            delta = -1.0 if S < K else 0.0
        return Greeks(delta=delta, gamma=0.0, vega=0.0, theta=0.0)

    d1, d2 = d1_d2(S, K, T, r, sigma)
    pdf_d1 = norm_pdf(d1)
    sqrt_T = math.sqrt(T)

    if params.option_type == "call":
        delta = norm_cdf(d1)
    else:
        delta = norm_cdf(d1) - 1.0

    gamma = pdf_d1 / (S * sigma * sqrt_T)
    vega = (S * pdf_d1 * sqrt_T) / 100.0

    theta_common = -(S * pdf_d1 * sigma) / (2.0 * sqrt_T)
    if params.option_type == "call":
        theta_annual = theta_common - r * K * math.exp(-r * T) * norm_cdf(d2)
    else:
        theta_annual = theta_common + r * K * math.exp(-r * T) * norm_cdf(-d2)
    theta = theta_annual / 365.0

    return Greeks(delta=delta, gamma=gamma, vega=vega, theta=theta)
