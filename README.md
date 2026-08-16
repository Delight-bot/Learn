# QuantLab

QuantLab is an interactive, educational options-pricing application. Instead
of reading definitions, you enter an option scenario, price it with two
independent methods (Black-Scholes and Monte Carlo simulation), inspect the
Greeks, and then change market assumptions to see how the price and Greeks
respond.

**This is an educational tool, not financial advice.** Nothing here should be
used to make real trading decisions.

## Table of Contents

1. [What QuantLab does](#1-what-quantlab-does)
2. [Why options need quantitative pricing models](#2-why-options-need-quantitative-pricing-models)
3. [Black-Scholes methodology](#3-black-scholes-methodology)
4. [Monte Carlo methodology](#4-monte-carlo-methodology)
5. [The Greeks](#5-the-greeks)
6. [Real SPY market data](#6-real-spy-market-data)
7. [Mathematical assumptions](#7-mathematical-assumptions)
8. [Application architecture](#8-application-architecture)
9. [Validation and testing](#9-validation-and-testing)
10. [Running the project locally](#10-running-the-project-locally)
11. [Limitations and future work](#11-limitations-and-future-work)

## 1. What QuantLab does

- Lets you enter an option scenario: stock price, strike, days to expiration,
  volatility, risk-free rate, and call/put.
- Prices it two ways: a closed-form **Black-Scholes** price, and an
  independently-simulated **Monte Carlo** price, so you can see two different
  mathematical approaches agree.
- Computes the **Greeks** (Delta, Gamma, Vega, Theta) with beginner-friendly
  explanations of what each one means.
- Lets you explore **scenarios** (stock +/-$5, volatility +5%, one week
  passing) and see the actual price change next to the change a Greek would
  have predicted.
- Visualizes a sample of simulated price paths and how the Monte Carlo
  estimate **converges** to the Black-Scholes price as the simulation count
  grows.
- Poses small **prediction challenges** before revealing the answer, so you
  test your intuition against the math.
- Grounds all of the above in **real SPY market data** (not just
  hypothetical scenarios): 30 years of actual daily prices, volatility
  computed from real historical returns, and a real 2020-2022 EOD option
  chain to compare the model's price directly against what the market
  actually quoted.

## 2. Why options need quantitative pricing models

An option's payoff depends on where the stock price ends up, which is
unknown today. Its "fair" price is therefore not just the payoff — it's the
*expected*, risk-adjusted, discounted payoff over every possible future stock
price path. Getting that number requires a model of how stock prices move
(here, geometric Brownian motion) and a way to either solve the resulting
expectation in closed form (Black-Scholes) or estimate it numerically
(Monte Carlo). Quantitative models also produce the Greeks: precise,
consistent sensitivities that let you reason about risk without re-deriving
the price from scratch every time an input changes.

## 3. Black-Scholes methodology

Implemented from scratch in [`backend/quant/black_scholes.py`](backend/quant/black_scholes.py).

For a European option with spot price `S`, strike `K`, time to expiration `T`
(in years), risk-free rate `r`, and volatility `sigma`:

```
d1 = [ln(S / K) + (r + sigma^2 / 2) * T] / (sigma * sqrt(T))
d2 = d1 - sigma * sqrt(T)

Call price = S * N(d1) - K * exp(-r * T) * N(d2)
Put price  = K * exp(-r * T) * N(-d2) - S * N(-d1)
```

where `N(.)` is the standard normal CDF. This assumes the stock price follows
geometric Brownian motion under the risk-neutral measure, so the discounted
expected payoff has a closed-form solution.

## 4. Monte Carlo methodology

Implemented from scratch with NumPy in [`backend/quant/monte_carlo.py`](backend/quant/monte_carlo.py).

Rather than solving the expectation analytically, Monte Carlo simulates many
possible terminal stock prices under the same risk-neutral dynamics:

```
S_T = S_0 * exp((r - 0.5 * sigma^2) * T + sigma * sqrt(T) * Z),   Z ~ N(0, 1)

payoff = max(S_T - K, 0)   for a call
payoff = max(K - S_T, 0)   for a put

price = exp(-r * T) * mean(payoff)
```

The standard error of the estimate is `exp(-r*T) * std(payoff) / sqrt(n)`,
which shrinks as the number of simulations `n` grows — this is the
convergence the app visualizes. The path chart plots a small sample (50-100)
of full simulated paths for intuition; the pricing estimate itself can use up
to 100,000 simulated terminal prices without plotting all of them.

## 5. The Greeks

Implemented analytically (not via finite differences) in
[`backend/quant/greeks.py`](backend/quant/greeks.py), derived directly from
the Black-Scholes formula:

| Greek | Meaning | Formula |
|---|---|---|
| Delta | Price change per $1 move in the stock | `N(d1)` (call), `N(d1) - 1` (put) |
| Gamma | How fast Delta changes as the stock moves | `N'(d1) / (S * sigma * sqrt(T))` |
| Vega | Price change per 1 percentage-point move in volatility | `S * N'(d1) * sqrt(T) / 100` |
| Theta | Price change per calendar day, as time passes | see `greeks.py` docstring |

`N'(.)` is the standard normal PDF. The app's unit tests cross-check every
Greek against a finite-difference approximation of the Black-Scholes price to
catch any drift between the closed-form derivative and the price function.

## 6. Real SPY market data

QuantLab pairs the pricing engine with two real datasets sourced from
Kaggle, so scenarios can be grounded in actual market history instead of
only user-typed hypotheticals:

- **SPY daily price history (1993-2023)** — [seansaliga/spy-start-10312023](https://www.kaggle.com/datasets/seansaliga/spy-start-10312023),
  ~7,800 trading days of OHLCV. Shipped as-is at
  `backend/data/processed/spy_price_history.csv`.
- **SPY EOD option chains (2020-2022)** — [kylegraupe/spy-daily-eod-options-quotes-2020-2022](https://www.kaggle.com/datasets/kylegraupe/spy-daily-eod-options-quotes-2020-2022),
  full daily chains (strike, expiry, bid/ask/last, IV, market-computed
  Greeks) for both calls and puts. The raw dataset is ~1.27GB across 3.6M
  rows; `backend/scripts/process_options_data.py` filters it down to
  near-the-money, short-dated contracts (DTE ≤ 60, within 10% of spot) —
  the ones a teaching tool would actually show — producing a ~940K-row,
  32MB Parquet file at `backend/data/processed/spy_options_chain.parquet`
  that ships with the repo. Re-run the script if you want a different cut
  of the raw data (see the script for the raw-data download path).

This real data feeds three things in the app, all in
[`backend/quant/historical.py`](backend/quant/historical.py):

1. **Price history chart** — the full 30-year SPY close series.
2. **Realized volatility** — an annualized volatility computed directly
   from trailing daily log returns (`std(log returns) * sqrt(252)`), as a
   real alternative to guessing sigma. Picking a date near the March 2020
   COVID crash, for example, surfaces realized volatility upward of 60-80%
   — dramatically higher than typical pre-crash levels — which you can
   load straight into the pricer.
3. **Model vs. market comparison** — pick a real trading day and
   expiration, pick a strike from the actual chain, and QuantLab prices
   that exact contract two ways: once using the *market's own implied
   volatility* (should land close to the real market mid-price, which is
   a useful correctness check on the model itself), and once using
   *realized volatility* computed with no knowledge of the option market
   at all. The gap between those two is a concrete illustration of the
   difference between backward-looking realized volatility and the
   market's forward-looking, risk-adjusted expectation (implied
   volatility).

Because the option dataset only covers 2020-2022 and the risk-free rate
isn't part of either dataset, the comparison endpoint uses a
user-adjustable constant `r` (default 2%) rather than a real historical
rate series — a known simplification, noted again in
[Limitations](#11-limitations-and-future-work).

## 7. Mathematical assumptions

Black-Scholes and this Monte Carlo implementation both assume:

- The underlying follows geometric Brownian motion with constant volatility.
- The risk-free rate is constant over the option's life.
- No dividends, transaction costs, or taxes.
- European exercise only (no early exercise, unlike American options).
- Markets are frictionless and continuous trading is possible.

These are simplifications. Real markets exhibit volatility that changes over
time and with strike (the "volatility smile"), discrete dividends, and
transaction costs — all deliberately out of scope for this MVP.

## 8. Application architecture

```
React frontend  --HTTP/JSON-->  FastAPI  -->  Python quantitative engine
```

```
backend/
    main.py              FastAPI app and route handlers
    models.py             Pydantic request/response models
    quant/
        black_scholes.py  Black-Scholes pricing (from scratch)
        monte_carlo.py     Monte Carlo pricing + path simulation (from scratch)
        greeks.py          Analytical Greeks
        historical.py      Loads/queries real SPY price history + option chain data
    scripts/
        process_options_data.py   One-off filter: raw Kaggle CSV -> shipped Parquet
    data/
        processed/         Shipped datasets (price history CSV, option chain Parquet)
        raw/                Untracked raw Kaggle downloads (gitignored)
    tests/                 pytest suite for the quant engine + historical module

frontend/
    src/
        components/        UI building blocks (inputs, dashboards, charts)
        services/api.ts     Typed fetch wrappers around the FastAPI endpoints
        types/               Shared request/response types
        App.tsx             Top-level layout and state
```

Route handlers in `main.py` only translate between HTTP and the pure
`quant.*` functions — all pricing math lives in `quant/`, independent of the
web framework, so it can be tested and reused directly. `quant/historical.py`
follows the same rule: it only loads and queries real data, it doesn't price
anything itself — `main.py` wires a historical quote into `black_scholes.py`
to produce the model-vs-market comparison.

### API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/black-scholes` | Theoretical price, d1, d2 |
| `POST /api/greeks` | Delta, Gamma, Vega, Theta with explanations |
| `POST /api/monte-carlo` | MC price, standard error, sample paths, convergence series |
| `POST /api/scenario` | Before/after price for a predefined scenario, plus the Greek-based estimate |
| `GET /api/historical/price-history` | Real SPY daily closes over a date range |
| `GET /api/historical/realized-volatility` | Annualized realized vol from trailing real returns |
| `GET /api/historical/quote-dates` | Trading days available in the option-chain sample |
| `GET /api/historical/expirations` | Expirations available for a given quote date |
| `GET /api/historical/option-chain` | Real strikes/bid/ask/last/IV for a quote date + expiration |
| `POST /api/historical/compare` | Model price (market IV and realized vol) vs. real market quote |

## 9. Validation and testing

49 pytest tests in `backend/tests/` cover:

- Black-Scholes call/put prices against independently-computed reference
  values.
- **Put-call parity**: `C - P = S - K * exp(-rT)`, checked across multiple
  scenarios.
- Monte Carlo pricing converging to the Black-Scholes price as simulation
  count grows (checked both by a direct comparison within several standard
  errors, and by a decreasing-error convergence series).
- Every Greek checked against a finite-difference approximation of the
  Black-Scholes price function.
- Edge cases: near-zero time to expiration, very low volatility, deep
  in-the-money and deep out-of-the-money options.
- A fixed random seed is used wherever Monte Carlo results are asserted on,
  so those tests are reproducible.
- The historical-data module: real price lookups, realized volatility on a
  known calm date and a known crash date (asserting the crash produces
  higher volatility), option-chain queries, and error handling for
  dates/strikes outside the data.

Run them with `pytest` from `backend/` (see below).

## 10. Running the project locally

### Prerequisites

- Python 3.11+
- Node.js 18+

The real SPY datasets (`backend/data/processed/`) are committed to the
repo, so no Kaggle account or re-download is needed to run the app.

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
pytest                 # run the quant engine test suite
uvicorn main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at
`http://localhost:8000/docs`).

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend expects the API at
`http://localhost:8000` by default; override with a `VITE_API_BASE_URL` env
var (e.g. in `frontend/.env.local`) if needed.

## 11. Limitations and future work

Historical SPY price data, real 2020-2022 option chains, and a model-vs-market
comparison are now implemented (see [section 6](#6-real-spy-market-data)) —
originally deferred future features, now in the MVP. Known limitations of
that data integration:

- The option-chain sample is filtered to short-dated, near-the-money
  contracts (DTE ≤ 60, within 10% of spot) to keep the shipped dataset a
  reasonable size — far OTM/ITM and long-dated (LEAPS) contracts from the
  2020-2022 window aren't queryable.
- The risk-free rate `r` used in the model-vs-market comparison is a
  user-adjustable constant, not a real historical rate series (neither
  Kaggle dataset includes one), so `r` is a simplification even when
  everything else in the comparison is real data.
- Coverage is SPY-only and stops at end of 2022 (options) / end of 2023
  (price history) — whatever the underlying Kaggle datasets cover.

Still intentionally out of scope for this MVP (see the code for where these
would plug in):

- An implied volatility solver (Newton-Raphson or bisection) — currently
  the app reads IV directly from the historical dataset rather than solving
  for it.
- A delta-hedging simulator.
- Portfolio-level P&L simulation.
- Volatility smile/surface visualization.
- Historical market scenario replay (e.g. "replay the 2020 crash" as a
  guided walkthrough, rather than picking dates manually).

The architecture (a pure Python `quant/` engine behind a thin FastAPI layer,
with `historical.py` kept separate from pricing) is intended to make these
additive rather than requiring a rewrite.
