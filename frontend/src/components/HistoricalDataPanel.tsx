import { Card } from "./Card";
import { PriceHistoryChart } from "./PriceHistoryChart";
import { RealizedVolExplorer } from "./RealizedVolExplorer";
import { MarketComparison } from "./MarketComparison";

interface Props {
  onApplyRealizedVol: (S: number, sigma: number) => void;
}

export function HistoricalDataPanel({ onApplyRealizedVol }: Props) {
  return (
    <Card
      title="Real SPY Market Data"
      subtitle="Grounded in actual history, not just hypothetical scenarios: SPY daily prices (1993-2023) and a real EOD option-chain sample (2020-2022), via Kaggle."
    >
      <div className="space-y-6">
        <div>
          <p className="text-sm text-slate-300 mb-2">30 years of SPY closing prices</p>
          <PriceHistoryChart />
        </div>

        <RealizedVolExplorer onApply={onApplyRealizedVol} />

        <div className="pt-2 border-t border-slate-800">
          <p className="text-sm font-medium text-slate-200 mb-3">Model vs. Real Market Quotes</p>
          <MarketComparison />
        </div>
      </div>
    </Card>
  );
}
