import { useState } from "react";
import { fetchRealizedVolatility } from "../services/api";
import type { RealizedVolatilityResponse } from "../types/historical";

const MIN_DATE = "1993-01-29";
const MAX_DATE = "2023-12-27";
const DEFAULT_DATE = "2020-03-20"; // COVID crash -- a striking realized-vol example

interface Props {
  onApply: (S: number, sigma: number) => void;
}

export function RealizedVolExplorer({ onApply }: Props) {
  const [date, setDate] = useState(DEFAULT_DATE);
  const [windowDays, setWindowDays] = useState(30);
  const [result, setResult] = useState<RealizedVolatilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchRealizedVolatility(date, windowDays);
      setResult(res);
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : "No SPY price data for that date (markets closed, or outside 1993-2023 range).");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
      <p className="text-sm text-slate-300 mb-3">
        Compute real SPY volatility from actual historical returns, instead of guessing a sigma.
      </p>
      <div className="flex flex-wrap items-end gap-3 mb-3">
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Date</label>
          <input
            type="date"
            className="input"
            min={MIN_DATE}
            max={MAX_DATE}
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">Trailing window (days)</label>
          <select className="input" value={windowDays} onChange={(e) => setWindowDays(Number(e.target.value))}>
            {[10, 20, 30, 60, 90].map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="rounded-lg py-2 px-4 text-sm font-medium bg-emerald-500/15 border border-emerald-500 text-emerald-300 hover:bg-emerald-500/25 transition-colors disabled:opacity-50"
        >
          {loading ? "Computing…" : "Compute Realized Vol"}
        </button>
      </div>

      {error && <p className="text-sm text-rose-400">{error}</p>}

      {result && (
        <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-slate-800">
          <div>
            <p className="text-xs text-slate-500">SPY Close on {result.date}</p>
            <p className="text-lg font-semibold text-slate-100">${result.spy_close.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">{result.window_days}-day Realized Volatility</p>
            <p className="text-lg font-semibold text-sky-400">{(result.annualized_volatility * 100).toFixed(1)}%</p>
          </div>
          <button
            onClick={() => onApply(result.spy_close, result.annualized_volatility)}
            className="ml-auto text-sm text-emerald-400 hover:text-emerald-300"
          >
            Load into pricer →
          </button>
        </div>
      )}
    </div>
  );
}
