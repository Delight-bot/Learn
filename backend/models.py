"""Pydantic request/response models for the QuantLab API.

All monetary/rate inputs are decimals from the caller's point of view:
sigma=0.20 means 20% annualized volatility, r=0.045 means 4.5%. The
frontend is responsible for converting user-facing percentage inputs
into these decimals before calling the API.
"""

from typing import Literal

from pydantic import BaseModel, Field

OptionType = Literal["call", "put"]

ScenarioName = Literal["stock_up_5", "stock_down_5", "vol_up_5", "time_passes_1w"]


class OptionRequest(BaseModel):
    S: float = Field(gt=0, description="Current stock price")
    K: float = Field(gt=0, description="Strike price")
    days_to_expiration: float = Field(ge=0, description="Days until expiration")
    sigma: float = Field(ge=0, le=5, description="Annualized volatility, as a decimal (0.20 = 20%)")
    r: float = Field(ge=-0.5, le=1, description="Risk-free rate, as a decimal (0.045 = 4.5%)")
    option_type: OptionType

    @property
    def T(self) -> float:
        return self.days_to_expiration / 365.0


class BlackScholesResponse(BaseModel):
    price: float
    d1: float
    d2: float


class GreekExplanation(BaseModel):
    value: float
    explanation: str


class GreeksResponse(BaseModel):
    delta: GreekExplanation
    gamma: GreekExplanation
    vega: GreekExplanation
    theta: GreekExplanation


class MonteCarloRequest(OptionRequest):
    n_simulations: int = Field(default=10_000, description="Number of Monte Carlo simulations")
    seed: int | None = Field(default=None, description="Optional RNG seed for reproducibility")


class ConvergencePoint(BaseModel):
    n_simulations: int
    price: float


class MonteCarloResponse(BaseModel):
    black_scholes_price: float
    monte_carlo_price: float
    absolute_difference: float
    std_error: float
    n_simulations: int
    sample_paths: list[list[float]]
    time_grid: list[float]
    convergence: list[ConvergencePoint]


class ScenarioRequest(BaseModel):
    base: OptionRequest
    scenario: ScenarioName


class ScenarioResponse(BaseModel):
    label: str
    original_price: float
    new_price: float
    difference: float
    greek_used: str
    greek_value: float
    greek_estimated_difference: float


# ---------------------------------------------------------------------------
# Historical SPY data
# ---------------------------------------------------------------------------


class PricePoint(BaseModel):
    date: str
    close: float


class PriceHistoryResponse(BaseModel):
    start: str
    end: str
    points: list[PricePoint]


class RealizedVolatilityResponse(BaseModel):
    date: str
    window_days: int
    annualized_volatility: float
    spy_close: float


class OptionChainRow(BaseModel):
    strike: float
    dte: float
    underlying_last: float
    c_last: float | None
    c_bid: float | None
    c_ask: float | None
    c_iv: float | None
    p_last: float | None
    p_bid: float | None
    p_ask: float | None
    p_iv: float | None


class OptionChainResponse(BaseModel):
    quote_date: str
    expire_date: str
    underlying_last: float
    rows: list[OptionChainRow]


class ModelVsMarketRequest(BaseModel):
    quote_date: str
    expire_date: str
    strike: float
    option_type: OptionType
    r: float = Field(default=0.02, ge=-0.5, le=1, description="Risk-free rate assumption (decimal)")
    realized_vol_window_days: int = Field(default=30, ge=2, le=252)


class ModelVsMarketResponse(BaseModel):
    quote_date: str
    expire_date: str
    strike: float
    option_type: OptionType
    dte: float
    underlying_last: float

    market_last: float | None
    market_bid: float | None
    market_ask: float | None
    market_mid: float | None
    market_implied_vol: float | None

    model_price_using_market_iv: float | None
    realized_volatility: float
    model_price_using_realized_vol: float

    market_vs_model_iv_diff: float | None
    market_vs_model_realized_vol_diff: float | None
