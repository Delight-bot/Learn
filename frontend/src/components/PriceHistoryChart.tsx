import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchPriceHistory } from "../services/api";
import type { PricePoint } from "../types/historical";

export function PriceHistoryChart() {
  const [points, setPoints] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPriceHistory()
      .then((res) => {
        // Downsample for a snappy chart -- daily granularity isn't needed
        // to see the shape of 30 years of price history.
        const step = Math.max(1, Math.floor(res.points.length / 800));
        setPoints(res.points.filter((_, i) => i % step === 0));
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="h-48 bg-slate-950 border border-slate-800 rounded-lg animate-pulse" />;
  }

  return (
    <div className="h-48">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickFormatter={(d: string) => d.slice(0, 4)} minTickGap={40} />
          <YAxis stroke="#64748b" fontSize={11} width={48} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", fontSize: 12 }}
            formatter={(v) => [`$${Number(v).toFixed(2)}`, "SPY Close"]}
          />
          <Line dataKey="close" stroke="#38bdf8" strokeWidth={1.5} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
