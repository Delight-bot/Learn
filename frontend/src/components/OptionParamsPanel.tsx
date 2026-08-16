import { useState } from "react";
import type { OptionRequest } from "../types/option";
import { Card } from "./Card";

const GLOSSARY: { symbol: string; name: string; description: string }[] = [
  { symbol: "S", name: "Stock Price", description: "The current market price of the underlying stock." },
  { symbol: "K", name: "Strike Price", description: "The price at which the option holder can buy (call) or sell (put) the stock." },
  { symbol: "T", name: "Time to Expiration", description: "The time remaining until the option expires, measured in years." },
  { symbol: "r", name: "Risk-Free Rate", description: "The theoretical return of a riskless investment, like a short-term Treasury bill." },
  { symbol: "sigma (σ)", name: "Volatility", description: "How much the stock's returns fluctuate. Higher volatility means a wider range of possible future prices." },
];

interface Props {
  value: OptionRequest;
  onChange: (value: OptionRequest) => void;
}

export function OptionParamsPanel({ value, onChange }: Props) {
  const [showGlossary, setShowGlossary] = useState(false);

  function update<K extends keyof OptionRequest>(key: K, val: OptionRequest[K]) {
    onChange({ ...value, [key]: val });
  }

  return (
    <Card title="Option Parameters" subtitle="Enter a scenario to price.">
      <div className="space-y-4">
        <Field label="Stock Price (S)" prefix="$">
          <input
            type="number"
            className="input"
            value={value.S}
            onChange={(e) => update("S", Number(e.target.value))}
          />
        </Field>

        <Field label="Strike Price (K)" prefix="$">
          <input
            type="number"
            className="input"
            value={value.K}
            onChange={(e) => update("K", Number(e.target.value))}
          />
        </Field>

        <Field label="Days to Expiration">
          <input
            type="number"
            className="input"
            value={value.days_to_expiration}
            onChange={(e) => update("days_to_expiration", Number(e.target.value))}
          />
        </Field>

        <Field label="Volatility (σ)" suffix="%">
          <input
            type="number"
            step="0.5"
            className="input"
            value={value.sigma * 100}
            onChange={(e) => update("sigma", Number(e.target.value) / 100)}
          />
        </Field>

        <Field label="Risk-Free Rate (r)" suffix="%">
          <input
            type="number"
            step="0.1"
            className="input"
            value={value.r * 100}
            onChange={(e) => update("r", Number(e.target.value) / 100)}
          />
        </Field>

        <div>
          <label className="text-sm text-slate-400 mb-1.5 block">Option Type</label>
          <div className="grid grid-cols-2 gap-2">
            {(["call", "put"] as const).map((type) => (
              <button
                key={type}
                onClick={() => update("option_type", type)}
                className={`rounded-lg py-2 text-sm font-medium capitalize border transition-colors ${
                  value.option_type === type
                    ? "bg-emerald-500/15 border-emerald-500 text-emerald-300"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        <div className="pt-2 border-t border-slate-800">
          <button
            onClick={() => setShowGlossary((s) => !s)}
            className="text-sm text-emerald-400 hover:text-emerald-300"
          >
            {showGlossary ? "Hide" : "What do these variables mean?"}
          </button>
          {showGlossary && (
            <dl className="mt-3 space-y-2.5">
              {GLOSSARY.map((item) => (
                <div key={item.symbol}>
                  <dt className="text-sm font-medium text-slate-200">
                    {item.symbol} &mdash; {item.name}
                  </dt>
                  <dd className="text-xs text-slate-400 mt-0.5">{item.description}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      </div>
    </Card>
  );
}

function Field({
  label,
  prefix,
  suffix,
  children,
}: {
  label: string;
  prefix?: string;
  suffix?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="text-sm text-slate-400 mb-1.5 block">{label}</label>
      <div className="relative">
        {prefix && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">
            {prefix}
          </span>
        )}
        <div className={prefix ? "pl-6" : suffix ? "pr-6" : ""}>{children}</div>
        {suffix && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}
