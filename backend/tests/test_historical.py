import pytest

from quant import historical


def test_price_history_range_covers_known_span():
    start, end = historical.price_history_range()
    assert start <= "1993-02-01"
    assert end >= "2023-12-01"


def test_get_price_on_known_date():
    # From the raw dataset: 1993-01-29 close = 43.9375
    price = historical.get_price_on_date("1993-01-29")
    assert price == pytest.approx(43.9375, abs=1e-4)


def test_get_price_on_unknown_date_raises():
    with pytest.raises(historical.DateNotFoundError):
        historical.get_price_on_date("1776-07-04")


def test_get_price_series_respects_date_range():
    points = historical.get_price_series(start="2020-01-01", end="2020-01-31")
    assert len(points) > 0
    assert all("2020-01" in p["date"] for p in points)


def test_realized_volatility_is_positive_and_reasonable():
    # A calm-ish pre-COVID window; realized vol should be well under 100%.
    result = historical.realized_volatility("2019-12-31", window_days=30)
    assert 0 < result.annualized_volatility < 1.0


def test_realized_volatility_spikes_during_covid_crash():
    calm = historical.realized_volatility("2020-01-15", window_days=20)
    crash = historical.realized_volatility("2020-03-20", window_days=20)
    assert crash.annualized_volatility > calm.annualized_volatility


def test_realized_volatility_unknown_date_raises():
    with pytest.raises(historical.DateNotFoundError):
        historical.realized_volatility("1776-07-04")


def test_available_quote_dates_nonempty_and_sorted():
    dates = historical.available_quote_dates()
    assert len(dates) > 0
    assert dates == sorted(dates)


def test_available_expirations_for_first_quote_date():
    dates = historical.available_quote_dates()
    expirations = historical.available_expirations(dates[0])
    assert len(expirations) > 0


def test_available_expirations_unknown_date_raises():
    with pytest.raises(historical.DateNotFoundError):
        historical.available_expirations("1776-07-04")


def test_option_chain_rows_share_quote_and_expire_date():
    dates = historical.available_quote_dates()
    quote_date = dates[len(dates) // 2]
    expire_date = historical.available_expirations(quote_date)[0]
    rows = historical.get_option_chain(quote_date, expire_date)
    assert len(rows) > 0
    assert all(r["quote_date"] == quote_date for r in rows)
    assert all(r["expire_date"] == expire_date for r in rows)


def test_option_chain_unknown_combo_raises():
    with pytest.raises(historical.DateNotFoundError):
        historical.get_option_chain("1776-07-04", "1776-08-04")


def test_get_option_quote_matches_a_known_row():
    dates = historical.available_quote_dates()
    quote_date = dates[len(dates) // 2]
    expire_date = historical.available_expirations(quote_date)[0]
    rows = historical.get_option_chain(quote_date, expire_date)
    target_strike = rows[len(rows) // 2]["strike"]

    quote = historical.get_option_quote(quote_date, expire_date, target_strike)
    assert quote["strike"] == pytest.approx(target_strike)


def test_get_option_quote_unknown_strike_raises():
    dates = historical.available_quote_dates()
    quote_date = dates[0]
    expire_date = historical.available_expirations(quote_date)[0]
    with pytest.raises(historical.DateNotFoundError):
        historical.get_option_quote(quote_date, expire_date, strike=-999.0)
