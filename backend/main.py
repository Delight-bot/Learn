"""FastAPI app exposing the QuantLab quantitative engine.

Route handlers only translate between HTTP/Pydantic models and the pure
quant.* functions -- no pricing math lives here.
"""

import math

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    BlackScholesResponse,
    ConvergencePoint,
    GreekExplanation,
    GreeksResponse,
    ModelVsMarketRequest,
    ModelVsMarketResponse,
    MonteCarloRequest,
    MonteCarloResponse,
    OptionChainResponse,
    OptionChainRow,
    OptionRequest,
    PriceHistoryResponse,
    PricePoint,
    RealizedVolatilityResponse,
    ScenarioRequest,
    ScenarioResponse,
)
from quant import historical
from quant.black_scholes import OptionParams, black_scholes_price, d1_d2
from quant.greeks import compute_greeks
from quant.monte_carlo import convergence_series, monte_carlo_price

app = FastAPI(title="QuantLab API", description="Educational options-pricing engine.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://delight-bot.github.io",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

GREEK_EXPLANATIONS = {
    "delta": "Approximately how much the option price changes when the stock moves by $1.",
    "gamma": "How quickly Delta itself changes as the stock price moves.",
    "vega": "How sensitive the option is to changes in volatility (per 1 percentage-point move).",
    "theta": "How much value the option loses per calendar day as time passes.",
}


def _to_params(req: OptionRequest) -> OptionParams:
    return OptionParams(S=req.S, K=req.K, T=req.T, r=req.r, sigma=req.sigma, option_type=req.option_type)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/black-scholes", response_model=BlackScholesResponse)
def price_black_scholes(req: OptionRequest):
    params = _to_params(req)
    price = black_scholes_price(params)
    d1, d2 = d1_d2(params.S, params.K, params.T, params.r, params.sigma)
    return BlackScholesResponse(price=price, d1=d1, d2=d2)


@app.post("/api/greeks", response_model=GreeksResponse)
def get_greeks(req: OptionRequest):
    params = _to_params(req)
    g = compute_greeks(params)
    return GreeksResponse(
        delta=GreekExplanation(value=g.delta, explanation=GREEK_EXPLANATIONS["delta"]),
        gamma=GreekExplanation(value=g.gamma, explanation=GREEK_EXPLANATIONS["gamma"]),
        vega=GreekExplanation(value=g.vega, explanation=GREEK_EXPLANATIONS["vega"]),
        theta=GreekExplanation(value=g.theta, explanation=GREEK_EXPLANATIONS["theta"]),
    )


@app.post("/api/monte-carlo", response_model=MonteCarloResponse)
def price_monte_carlo(req: MonteCarloRequest):
    params = _to_params(req)
    bs_price = black_scholes_price(params)

    n_plot_steps = 100
    mc_result = monte_carlo_price(
        params,
        n_simulations=req.n_simulations,
        n_plot_paths=60,
        n_plot_steps=n_plot_steps,
        seed=req.seed,
    )

    simulation_counts = sorted({100, 1_000, 10_000, req.n_simulations})
    conv = convergence_series(params, simulation_counts, seed=req.seed)

    time_grid = [i * (params.T / n_plot_steps) for i in range(n_plot_steps + 1)]

    return MonteCarloResponse(
        black_scholes_price=bs_price,
        monte_carlo_price=mc_result.price,
        absolute_difference=abs(mc_result.price - bs_price),
        std_error=mc_result.std_error,
        n_simulations=mc_result.n_simulations,
        sample_paths=mc_result.sample_paths.tolist(),
        time_grid=time_grid,
        convergence=[ConvergencePoint(**point) for point in conv],
    )


SCENARIOS = {
    "stock_up_5": {"label": "Stock price +$5", "field": "S", "delta_value": 5.0, "greek": "delta"},
    "stock_down_5": {"label": "Stock price -$5", "field": "S", "delta_value": -5.0, "greek": "delta"},
    "vol_up_5": {"label": "Volatility +5%", "field": "sigma", "delta_value": 0.05, "greek": "vega"},
    "time_passes_1w": {"label": "One week passes", "field": "days_to_expiration", "delta_value": -7.0, "greek": "theta"},
}


@app.post("/api/scenario", response_model=ScenarioResponse)
def run_scenario(req: ScenarioRequest):
    config = SCENARIOS[req.scenario]
    original_params = _to_params(req.base)
    original_price = black_scholes_price(original_params)
    original_greeks = compute_greeks(original_params)

    new_data = req.base.model_dump()
    field = config["field"]
    new_value = new_data[field] + config["delta_value"]
    if field == "days_to_expiration":
        new_value = max(new_value, 0.0)
    if field == "sigma":
        new_value = max(new_value, 0.0)
    new_data[field] = new_value
    new_params = _to_params(OptionRequest(**new_data))
    new_price = black_scholes_price(new_params)

    greek_name = config["greek"]
    greek_value = getattr(original_greeks, greek_name)

    if greek_name == "delta":
        estimated_diff = greek_value * config["delta_value"]
    elif greek_name == "vega":
        # vega is per 1 percentage point; delta_value is a decimal (0.05 = 5 points)
        estimated_diff = greek_value * (config["delta_value"] * 100)
    else:  # theta, per calendar day; delta_value is in days
        estimated_diff = greek_value * (-config["delta_value"])

    return ScenarioResponse(
        label=config["label"],
        original_price=original_price,
        new_price=new_price,
        difference=new_price - original_price,
        greek_used=greek_name,
        greek_value=greek_value,
        greek_estimated_difference=estimated_diff,
    )


# ---------------------------------------------------------------------------
# Historical SPY data (real market data, not user-provided scenarios)
# ---------------------------------------------------------------------------


def _clean_float(value) -> float | None:
    """NaN (from missing quotes in the historical dataset) -> None."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


@app.get("/api/historical/price-history", response_model=PriceHistoryResponse)
def price_history(start: str | None = None, end: str | None = None):
    data_start, data_end = historical.price_history_range()
    points = historical.get_price_series(start, end)
    return PriceHistoryResponse(
        start=start or data_start,
        end=end or data_end,
        points=[PricePoint(**p) for p in points],
    )


@app.get("/api/historical/realized-volatility", response_model=RealizedVolatilityResponse)
def realized_volatility(date: str, window_days: int = 30):
    try:
        result = historical.realized_volatility(date, window_days)
        spy_close = historical.get_price_on_date(date)
    except historical.DateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RealizedVolatilityResponse(
        date=result.date,
        window_days=result.window_days,
        annualized_volatility=result.annualized_volatility,
        spy_close=spy_close,
    )


@app.get("/api/historical/quote-dates", response_model=list[str])
def quote_dates():
    return historical.available_quote_dates()


@app.get("/api/historical/expirations", response_model=list[str])
def expirations(quote_date: str):
    try:
        return historical.available_expirations(quote_date)
    except historical.DateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/historical/option-chain", response_model=OptionChainResponse)
def option_chain(quote_date: str, expire_date: str):
    try:
        rows = historical.get_option_chain(quote_date, expire_date)
    except historical.DateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    underlying_last = rows[0]["underlying_last"]
    return OptionChainResponse(
        quote_date=quote_date,
        expire_date=expire_date,
        underlying_last=underlying_last,
        rows=[
            OptionChainRow(
                strike=r["strike"],
                dte=r["dte"],
                underlying_last=r["underlying_last"],
                c_last=_clean_float(r.get("c_last")),
                c_bid=_clean_float(r.get("c_bid")),
                c_ask=_clean_float(r.get("c_ask")),
                c_iv=_clean_float(r.get("c_iv")),
                p_last=_clean_float(r.get("p_last")),
                p_bid=_clean_float(r.get("p_bid")),
                p_ask=_clean_float(r.get("p_ask")),
                p_iv=_clean_float(r.get("p_iv")),
            )
            for r in rows
        ],
    )


@app.post("/api/historical/compare", response_model=ModelVsMarketResponse)
def compare_model_vs_market(req: ModelVsMarketRequest):
    try:
        quote = historical.get_option_quote(req.quote_date, req.expire_date, req.strike)
        rv = historical.realized_volatility(req.quote_date, req.realized_vol_window_days)
    except historical.DateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    prefix = "c_" if req.option_type == "call" else "p_"
    market_last = _clean_float(quote.get(f"{prefix}last"))
    market_bid = _clean_float(quote.get(f"{prefix}bid"))
    market_ask = _clean_float(quote.get(f"{prefix}ask"))
    market_iv = _clean_float(quote.get(f"{prefix}iv"))
    market_mid = (market_bid + market_ask) / 2 if market_bid is not None and market_ask is not None else None

    S = float(quote["underlying_last"])
    K = float(quote["strike"])
    T = float(quote["dte"]) / 365.0

    model_price_iv = None
    if market_iv is not None and market_iv > 0:
        params_iv = OptionParams(S=S, K=K, T=T, r=req.r, sigma=market_iv, option_type=req.option_type)
        model_price_iv = black_scholes_price(params_iv)

    params_rv = OptionParams(S=S, K=K, T=T, r=req.r, sigma=rv.annualized_volatility, option_type=req.option_type)
    model_price_rv = black_scholes_price(params_rv)

    return ModelVsMarketResponse(
        quote_date=req.quote_date,
        expire_date=req.expire_date,
        strike=K,
        option_type=req.option_type,
        dte=float(quote["dte"]),
        underlying_last=S,
        market_last=market_last,
        market_bid=market_bid,
        market_ask=market_ask,
        market_mid=market_mid,
        market_implied_vol=market_iv,
        model_price_using_market_iv=model_price_iv,
        realized_volatility=rv.annualized_volatility,
        model_price_using_realized_vol=model_price_rv,
        market_vs_model_iv_diff=(market_mid - model_price_iv) if (market_mid is not None and model_price_iv is not None) else None,
        market_vs_model_realized_vol_diff=(market_mid - model_price_rv) if market_mid is not None else None,
    )
