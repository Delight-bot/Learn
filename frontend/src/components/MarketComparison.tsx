import { useEffect, useMemo, useState } from "react";
import { fetchExpirations, fetchModelVsMarket, fetchOptionChain, fetchQuoteDates } from "../services/api";
import type { ModelVsMarketResponse, OptionChainRow } from "../types/historical";
import type { OptionType } from "../types/option";

function nearestDate(target: string, available: string[]): string {
  if (available.includes(target)) return target;
  let best = available[0];
  let bestDiff = Infinity;
  for (const d of available) {
    const diff = Math.abs(new Date(d).getTime() - new Date(target).getTime());
    if (diff < bestDiff) {
      bestDiff = diff;
      best = d;
    }
  }
  return best;
}

export function MarketComparison() {
  const [quoteDates, setQuoteDates] = useState<string[]>([]);
  const [quoteDate, setQuoteDate] = useState<string>("");
  const [expirations, setExpirations] = useState<string[]>([]);
  const [expireDate, setExpireDate] = useState<string>("");
  const [rows, setRows] = useState<OptionChainRow[]>([]);
  const [underlying, setUnderlying] = useState<number | null>(null);
  const [selected, setSelected] = useState<{ strike: number; type: OptionType } | null>(null);
  const [comparison, setComparison] = useState<ModelVsMarketResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchQuoteDates().then((dates) => {
      setQuoteDates(dates);
      const covidCrash = "2020-03-20";
      setQuoteDate(dates.includes(covidCrash) ? covidCrash : dates[Math.floor(dates.length / 2)]);
    });
  }, []);

  useEffect(() => {
    if (!quoteDate) return;
    fetchExpirations(quoteDate).then((exps) => {
      setExpirations(exps);
      setExpireDate(exps[Math.min(3, exps.length - 1)] ?? "");
    });
  }, [quoteDate]);

  useEffect(() => {
    if (!quoteDate || !expireDate) return;
    setLoading(true);
    setComparison(null);
    setSelected(null);
    fetchOptionChain(quoteDate, expireDate)
      .then((res) => {
        setRows(res.rows);
        setUnderlying(res.underlying_last);
      })
      .finally(() => setLoading(false));
  }, [quoteDate, expireDate]);

  const dateRange = useMemo(
    () => (quoteDates.length ? { min: quoteDates[0], max: quoteDates[quoteDates.length - 1] } : null),
    [quoteDates]
  );

  function handleDateInput(value: string) {
    if (quoteDates.length === 0) return;
    setQuoteDate(nearestDate(value, quoteDates));
  }

  async function compare(strike: number, type: OptionType) {
    setSelected({ strike, type });
    setComparison(null);
    const res = await fetchModelVsMarket({ quote_date: quoteDate, expire_date: expireDate, strike, option_type: type });
    setComparison(res);
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-300">
        Real SPY option quotes from {dateRange?.min} to {dateRange?.max}. Pick a trading day and expiration to see the
        actual market-quoted price next to what our Black-Scholes model produces.
      </p>

      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Quote Date</label>
          <input
            type="date"
            className="input"
            min={dateRange?.min}
            max={dateRange?.max}
            value={quoteDate}
            onChange={(e) => handleDateInput(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Expiration</label>
          <select className="input" value={expireDate} onChange={(e) => setExpireDate(e.target.value)}>
            {expirations.map((exp) => (
              <option key={exp} value={exp}>
                {exp}
              </option>
            ))}
          </select>
        </div>
        {underlying !== null && (
          <div>
            <p className="text-xs text-slate-500">SPY on this date</p>
            <p className="text-sm font-semibold text-slate-100">${underlying.toFixed(2)}</p>
          </div>
        )}
      </div>

      {loading && <p className="text-sm text-slate-500">Loading option chain…</p>}

      {!loading && rows.length > 0 && (
        <div className="overflow-x-auto border border-slate-800 rounded-lg">
          <table className="w-full text-xs">
            <thead className="bg-slate-950 text-slate-500">
              <tr>
                <th className="text-right px-2 py-1.5">Call Bid/Ask</th>
                <th className="text-right px-2 py-1.5">Call</th>
                <th className="text-center px-2 py-1.5">Strike</th>
                <th className="text-left px-2 py-1.5">Put</th>
                <th className="text-left px-2 py-1.5">Put Bid/Ask</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.strike} className="border-t border-slate-800 hover:bg-slate-900/60">
                  <td className="text-right px-2 py-1 text-slate-500">
                    {row.c_bid?.toFixed(2) ?? "—"} / {row.c_ask?.toFixed(2) ?? "—"}
                  </td>
                  <td className="text-right px-2 py-1">
                    <button
                      onClick={() => compare(row.strike, "call")}
                      className={`px-2 py-0.5 rounded ${
                        selected?.strike === row.strike && selected.type === "call"
                          ? "bg-emerald-500/20 text-emerald-300"
                          : "text-slate-300 hover:bg-slate-800"
                      }`}
                    >
                      {row.c_last?.toFixed(2) ?? "—"}
                    </button>
                  </td>
                  <td className="text-center px-2 py-1 font-medium text-slate-200">{row.strike.toFixed(1)}</td>
                  <td className="text-left px-2 py-1">
                    <button
                      onClick={() => compare(row.strike, "put")}
                      className={`px-2 py-0.5 rounded ${
                        selected?.strike === row.strike && selected.type === "put"
                          ? "bg-emerald-500/20 text-emerald-300"
                          : "text-slate-300 hover:bg-slate-800"
                      }`}
                    >
                      {row.p_last?.toFixed(2) ?? "—"}
                    </button>
                  </td>
                  <td className="text-left px-2 py-1 text-slate-500">
                    {row.p_bid?.toFixed(2) ?? "—"} / {row.p_ask?.toFixed(2) ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {comparison && (
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
          <p className="text-sm text-slate-200 mb-3">
            {comparison.quote_date} · {comparison.option_type} · strike ${comparison.strike.toFixed(1)} · expires{" "}
            {comparison.expire_date} ({comparison.dte.toFixed(0)}d)
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
            <Stat label="Market Mid" value={comparison.market_mid !== null ? `$${comparison.market_mid.toFixed(2)}` : "—"} />
            <Stat
              label="Model (market IV)"
              value={comparison.model_price_using_market_iv !== null ? `$${comparison.model_price_using_market_iv.toFixed(2)}` : "n/a"}
              sub={comparison.market_implied_vol !== null ? `IV ${(comparison.market_implied_vol * 100).toFixed(1)}%` : undefined}
            />
            <Stat
              label="Model (realized vol)"
              value={`$${comparison.model_price_using_realized_vol.toFixed(2)}`}
              sub={`vol ${(comparison.realized_volatility * 100).toFixed(1)}%`}
            />
            <Stat
              label="Market − Model (RV)"
              value={
                comparison.market_vs_model_realized_vol_diff !== null
                  ? `${comparison.market_vs_model_realized_vol_diff >= 0 ? "+" : ""}$${comparison.market_vs_model_realized_vol_diff.toFixed(2)}`
                  : "—"
              }
            />
          </div>
          <p className="text-xs text-slate-500 mt-3 pt-3 border-t border-slate-800 leading-snug">
            "Model (market IV)" feeds the market's own implied volatility into our Black-Scholes formula — it should
            land close to the market mid, confirming the model is internally consistent. "Model (realized vol)" instead
            uses volatility measured from actual trailing price history, with no knowledge of the option market at
            all — the gap between the two shows the difference between backward-looking realized volatility and the
            market's forward-looking expectation.
          </p>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-base font-semibold text-slate-100 mt-0.5">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
    </div>
  );
}
