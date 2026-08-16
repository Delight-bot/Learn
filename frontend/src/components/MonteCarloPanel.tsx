import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MonteCarloResponse, OptionRequest } from "../types/option";
import { fetchMonteCarlo } from "../services/api";
import { Card } from "./Card";

const SIM_COUNTS = [100, 1_000, 10_000, 100_000];

interface Props {
  params: OptionRequest;
}

export function MonteCarloPanel({ params }: Props) {
  const [nSims, setNSims] = useState(10_000);
  const [result, setResult] = useState<MonteCarloResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchMonteCarlo(params, nSims);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run simulation");
    } finally {
      setLoading(false);
    }
  }

  const pathData = result
    ? result.time_grid.map((t, i) => {
        const row: Record<string, number> = { t };
        result.sample_paths.forEach((path, pathIdx) => {
          row[`p${pathIdx}`] = path[i];
        });
        return row;
      })
    : [];

  return (
    <Card title="Monte Carlo Simulation" subtitle="Simulate terminal stock prices under risk-neutral GBM.">
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="text-sm text-slate-400 mb-1.5 block">Simulations</label>
          <select
            className="input"
            value={nSims}
            onChange={(e) => setNSims(Number(e.target.value))}
          >
            {SIM_COUNTS.map((n) => (
              <option key={n} value={n}>
                {n.toLocaleString()}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="rounded-lg py-2 px-4 text-sm font-medium bg-emerald-500/15 border border-emerald-500 text-emerald-300 hover:bg-emerald-500/25 transition-colors disabled:opacity-50"
        >
          {loading ? "Running…" : "Run Simulation"}
        </button>
      </div>

      {error && <p className="text-sm text-rose-400 mb-3">{error}</p>}

      {result && (
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-3 text-center">
            <Stat label="Black-Scholes Price" value={`$${result.black_scholes_price.toFixed(4)}`} />
            <Stat label="Monte Carlo Price" value={`$${result.monte_carlo_price.toFixed(4)}`} />
            <Stat label="Abs. Difference" value={`$${result.absolute_difference.toFixed(4)}`} />
          </div>
          <p className="text-xs text-slate-500 -mt-2">
            Standard error: ±${result.std_error.toFixed(4)} over {result.n_simulations.toLocaleString()} simulations
          </p>

          <div>
            <p className="text-sm text-slate-300 mb-2">
              Sample of {result.sample_paths.length} simulated price paths
            </p>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={pathData} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="t"
                    tickFormatter={(v: number) => v.toFixed(2)}
                    stroke="#64748b"
                    fontSize={11}
                    label={{ value: "Time (years)", position: "insideBottom", offset: -2, fill: "#64748b", fontSize: 11 }}
                  />
                  <YAxis stroke="#64748b" fontSize={11} width={48} />
                  {result.sample_paths.map((_, idx) => (
                    <Line
                      key={idx}
                      dataKey={`p${idx}`}
                      stroke="#38bdf8"
                      strokeOpacity={0.35}
                      dot={false}
                      isAnimationActive={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div>
            <p className="text-sm text-slate-300 mb-2">Convergence to Black-Scholes price</p>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={result.convergence} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="n_simulations"
                    scale="log"
                    domain={["auto", "auto"]}
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(v: number) => v.toLocaleString()}
                  />
                  <YAxis stroke="#64748b" fontSize={11} width={48} domain={["auto", "auto"]} />
                  <Tooltip
                    contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", fontSize: 12 }}
                    formatter={(value) => [`$${Number(value).toFixed(4)}`, "MC Price"]}
                    labelFormatter={(label) => `${Number(label).toLocaleString()} sims`}
                  />
                  <Line
                    dataKey="price"
                    stroke="#34d399"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-base font-semibold text-slate-100 mt-0.5">{value}</p>
    </div>
  );
}
