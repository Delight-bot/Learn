"""Historical SPY market data: real daily prices (1993-2023) and a curated
real EOD option-chain sample (2020-2022), both sourced from Kaggle.

This module only loads and queries real market data -- it does not price
anything itself. Pricing (Black-Scholes / Monte Carlo) still lives in
black_scholes.py / monte_carlo.py; main.py wires the two together so a
historical option quote can be priced with our own models and compared
against what the market actually quoted.

Data provenance:
    data/processed/spy_price_history.csv   Daily OHLCV, Kaggle dataset
        "SPY Daily Stock Info (01/1993 - 12/2023)" (seansaliga/spy-start-10312023)
    data/processed/spy_options_chain.parquet   Curated subset (DTE <= 60,
        |strike distance| <= 10%) of Kaggle dataset "$SPY Option Chains -
        Q1 2020 - Q4 2022" (kylegraupe/spy-daily-eod-options-quotes-2020-2022),
        reduced from ~3.6M to a shippable size by scripts/process_options_data.py.
"""

import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PRICE_HISTORY_PATH = DATA_DIR / "spy_price_history.csv"
OPTIONS_CHAIN_PATH = DATA_DIR / "spy_options_chain.parquet"

TRADING_DAYS_PER_YEAR = 252


@lru_cache(maxsize=1)
def _price_history() -> pd.DataFrame:
    df = pd.read_csv(PRICE_HISTORY_PATH, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    return df


@lru_cache(maxsize=1)
def _options_chain() -> pd.DataFrame:
    df = pd.read_parquet(OPTIONS_CHAIN_PATH)
    return df


def price_history_range() -> tuple[str, str]:
    df = _price_history()
    return df["date"].min().strftime("%Y-%m-%d"), df["date"].max().strftime("%Y-%m-%d")


def get_price_series(start: str | None = None, end: str | None = None) -> list[dict]:
    df = _price_history()
    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]
    return [
        {"date": row.date.strftime("%Y-%m-%d"), "close": float(row.close)}
        for row in df.itertuples()
    ]


class DateNotFoundError(ValueError):
    pass


def get_price_on_date(date: str) -> float:
    df = _price_history()
    match = df[df["date"] == date]
    if match.empty:
        raise DateNotFoundError(f"No SPY price data for {date}")
    return float(match.iloc[0]["close"])


@dataclass(frozen=True)
class RealizedVolResult:
    date: str
    window_days: int
    annualized_volatility: float


def realized_volatility(date: str, window_days: int = 30) -> RealizedVolResult:
    """Annualized realized volatility from trailing daily log returns,
    ending on (and including) the given date.
    """
    df = _price_history()
    idx = df.index[df["date"] == date]
    if len(idx) == 0:
        raise DateNotFoundError(f"No SPY price data for {date}")
    end_idx = idx[0]
    start_idx = max(0, end_idx - window_days + 1)
    window = df.iloc[start_idx : end_idx + 1]["log_return"].dropna()
    if len(window) < 2:
        raise ValueError("Not enough trading days in window to compute volatility")

    daily_std = float(window.std(ddof=1))
    annualized = daily_std * math.sqrt(TRADING_DAYS_PER_YEAR)
    return RealizedVolResult(date=date, window_days=window_days, annualized_volatility=annualized)


def available_quote_dates() -> list[str]:
    df = _options_chain()
    return sorted(df["quote_date"].unique().tolist())


def available_expirations(quote_date: str) -> list[str]:
    df = _options_chain()
    subset = df[df["quote_date"] == quote_date]
    if subset.empty:
        raise DateNotFoundError(f"No option chain data for quote date {quote_date}")
    return sorted(subset["expire_date"].unique().tolist())


def get_option_chain(quote_date: str, expire_date: str) -> list[dict]:
    df = _options_chain()
    subset = df[(df["quote_date"] == quote_date) & (df["expire_date"] == expire_date)]
    if subset.empty:
        raise DateNotFoundError(f"No option chain data for {quote_date} / {expire_date}")
    subset = subset.sort_values("strike")
    return subset.to_dict(orient="records")


def get_option_quote(quote_date: str, expire_date: str, strike: float) -> dict:
    df = _options_chain()
    subset = df[
        (df["quote_date"] == quote_date)
        & (df["expire_date"] == expire_date)
        & (np.isclose(df["strike"], strike))
    ]
    if subset.empty:
        raise DateNotFoundError(
            f"No option quote for {quote_date} / {expire_date} / strike {strike}"
        )
    return subset.iloc[0].to_dict()
