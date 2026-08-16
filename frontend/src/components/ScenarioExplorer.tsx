import { useState } from "react";
import type { OptionRequest, ScenarioName, ScenarioResponse } from "../types/option";
import { fetchScenario } from "../services/api";
import { Card } from "./Card";

const SCENARIOS: { key: ScenarioName; label: string }[] = [
  { key: "stock_up_5", label: "Stock price +$5" },
  { key: "stock_down_5", label: "Stock price -$5" },
  { key: "vol_up_5", label: "Volatility +5%" },
  { key: "time_passes_1w", label: "One week passes" },
];

interface Props {
  params: OptionRequest;
}

export function ScenarioExplorer({ params }: Props) {
  const [result, setResult] = useState<ScenarioResponse | null>(null);
  const [activeKey, setActiveKey] = useState<ScenarioName | null>(null);
  const [loading, setLoading] = useState(false);

  async function run(key: ScenarioName) {
    setActiveKey(key);
    setLoading(true);
    try {
      const res = await fetchScenario(params, key);
      setResult(res);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="Scenario Explorer" subtitle="See how a market change moves the option price.">
      <div className="grid grid-cols-2 gap-2 mb-4">
        {SCENARIOS.map((s) => (
          <button
            key={s.key}
            onClick={() => run(s.key)}
            className={`rounded-lg py-2 px-3 text-sm font-medium border transition-colors ${
              activeKey === s.key
                ? "bg-emerald-500/15 border-emerald-500 text-emerald-300"
                : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-slate-500">Calculating…</p>}

      {!loading && result && (
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-xs text-slate-500">Original Price</p>
              <p className="text-lg font-semibold text-slate-200">${result.original_price.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">New Price</p>
              <p className="text-lg font-semibold text-slate-200">${result.new_price.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Difference</p>
              <p className={`text-lg font-semibold ${result.difference >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {result.difference >= 0 ? "+" : ""}
                ${result.difference.toFixed(2)}
              </p>
            </div>
          </div>
          <p className="text-xs text-slate-500 pt-2 border-t border-slate-800">
            Estimated from {result.greek_used} ({result.greek_value.toFixed(4)}): a predicted change of{" "}
            <span className="text-slate-300">${result.greek_estimated_difference.toFixed(2)}</span> &mdash; close to the
            actual difference above because {result.greek_used} approximates the option's sensitivity to this change.
          </p>
        </div>
      )}
    </Card>
  );
}
