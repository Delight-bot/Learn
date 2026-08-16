import { useEffect, useState } from "react";
import { Header } from "./components/Header";
import { OptionParamsPanel } from "./components/OptionParamsPanel";
import { PriceDisplay } from "./components/PriceDisplay";
import { GreeksDashboard } from "./components/GreeksDashboard";
import { ScenarioExplorer } from "./components/ScenarioExplorer";
import { MonteCarloPanel } from "./components/MonteCarloPanel";
import { LearningChallenges } from "./components/LearningChallenges";
import { HistoricalDataPanel } from "./components/HistoricalDataPanel";
import { fetchBlackScholes, fetchGreeks, fetchMonteCarlo } from "./services/api";
import type { BlackScholesResponse, GreeksResponse, OptionRequest } from "./types/option";

const DEFAULT_PARAMS: OptionRequest = {
  S: 450,
  K: 460,
  days_to_expiration: 30,
  sigma: 0.2,
  r: 0.045,
  option_type: "call",
};

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(handle);
  }, [value, delayMs]);
  return debounced;
}

function App() {
  const [params, setParams] = useState<OptionRequest>(DEFAULT_PARAMS);
  const debouncedParams = useDebouncedValue(params, 300);

  const [bsResult, setBsResult] = useState<BlackScholesResponse | null>(null);
  const [greeks, setGreeks] = useState<GreeksResponse | null>(null);
  const [mcQuickPrice, setMcQuickPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      fetchBlackScholes(debouncedParams),
      fetchGreeks(debouncedParams),
      fetchMonteCarlo(debouncedParams, 1000),
    ])
      .then(([bs, g, mc]) => {
        if (cancelled) return;
        setBsResult(bs);
        setGreeks(g);
        setMcQuickPrice(mc.monte_carlo_price);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to reach the QuantLab API");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [debouncedParams]);

  return (
    <div className="min-h-screen">
      <Header />
      <main className="max-w-7xl mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        <div>
          <OptionParamsPanel value={params} onChange={setParams} />
        </div>

        <div className="space-y-6">
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/50 text-rose-300 text-sm rounded-lg p-4">
              {error}. Is the backend running at http://localhost:8000?
            </div>
          )}

          <PriceDisplay
            blackScholesPrice={bsResult?.price ?? null}
            monteCarloPrice={mcQuickPrice}
            loading={loading}
          />

          <GreeksDashboard greeks={greeks} loading={loading} />

          <ScenarioExplorer params={debouncedParams} />

          <MonteCarloPanel params={debouncedParams} />

          <LearningChallenges params={debouncedParams} greeks={greeks} />

          <HistoricalDataPanel
            onApplyRealizedVol={(S, sigma) => setParams((p) => ({ ...p, S, sigma }))}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
