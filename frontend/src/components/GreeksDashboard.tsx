import type { GreeksResponse } from "../types/option";
import { Card } from "./Card";

interface Props {
  greeks: GreeksResponse | null;
  loading: boolean;
}

export function GreeksDashboard({ greeks, loading }: Props) {
  const items = greeks
    ? [
        { key: "Delta", ...greeks.delta },
        { key: "Gamma", ...greeks.gamma },
        { key: "Vega", ...greeks.vega },
        { key: "Theta", ...greeks.theta },
      ]
    : [];

  return (
    <Card title="Greeks" subtitle="How the price reacts to each market input.">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {loading || !greeks
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-slate-950 border border-slate-800 rounded-lg p-4 h-24 animate-pulse" />
            ))
          : items.map((item) => (
              <div key={item.key} className="bg-slate-950 border border-slate-800 rounded-lg p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">{item.key}</p>
                <p className="text-xl font-semibold text-slate-100 mt-1">{item.value.toFixed(4)}</p>
                <p className="text-xs text-slate-500 mt-1.5 leading-snug">{item.explanation}</p>
              </div>
            ))}
      </div>
    </Card>
  );
}
