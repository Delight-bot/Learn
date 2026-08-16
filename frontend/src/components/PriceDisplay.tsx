import { Card } from "./Card";

interface Props {
  blackScholesPrice: number | null;
  monteCarloPrice: number | null;
  loading: boolean;
}

export function PriceDisplay({ blackScholesPrice, monteCarloPrice, loading }: Props) {
  return (
    <Card title="Theoretical Price">
      <div className="grid grid-cols-2 gap-4">
        <PriceTile label="Black-Scholes" value={blackScholesPrice} loading={loading} accent="emerald" />
        <PriceTile label="Monte Carlo" value={monteCarloPrice} loading={loading} accent="sky" />
      </div>
    </Card>
  );
}

function PriceTile({
  label,
  value,
  loading,
  accent,
}: {
  label: string;
  value: number | null;
  loading: boolean;
  accent: "emerald" | "sky";
}) {
  const color = accent === "emerald" ? "text-emerald-400" : "text-sky-400";
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`text-3xl font-semibold mt-1 ${color}`}>
        {loading || value === null ? "—" : `$${value.toFixed(2)}`}
      </p>
    </div>
  );
}
