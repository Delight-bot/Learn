import type { GreeksResponse, OptionRequest } from "../types/option";
import { Card } from "./Card";
import { PredictionChallenge } from "./PredictionChallenge";

interface Props {
  params: OptionRequest;
  greeks: GreeksResponse | null;
}

const STAY_SAME = "Stay approximately the same";
const INCREASE = "Increase in value";
const DECREASE = "Decrease in value";

export function LearningChallenges({ params, greeks }: Props) {
  if (!greeks) return null;

  const { S, K, option_type } = params;
  const newS = S + 5;
  const delta = greeks.delta.value;
  const vega = greeks.vega.value;
  const theta = greeks.theta.value;

  const deltaCorrectIndex = Math.abs(delta) < 0.01 ? 2 : delta > 0 ? 0 : 1;
  const vegaCorrectIndex = Math.abs(vega) < 0.0001 ? 2 : 0; // vega is non-negative for standard options
  const thetaCorrectIndex = Math.abs(theta) < 0.0001 ? 2 : theta < 0 ? 1 : 0;

  return (
    <Card title="Learning Challenges" subtitle="Predict before you peek — then see how the Greeks explain it.">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <PredictionChallenge
          question={`The stock rises from $${S.toFixed(0)} to $${newS.toFixed(0)}. What do you expect to happen to this ${option_type}?`}
          options={[INCREASE, DECREASE, STAY_SAME]}
          correctIndex={deltaCorrectIndex}
          explanation={`Delta is ${delta.toFixed(3)} here, meaning the price moves roughly $${Math.abs(delta).toFixed(2)} for every $1 move in the stock. With ${option_type === "call" ? "calls" : "puts"} this ${option_type === "call" ? "usually rises" : "usually falls"} as the stock rises.`}
        />

        <PredictionChallenge
          question="Volatility increases by 5 percentage points, with everything else held constant. What happens to the option's price?"
          options={[INCREASE, DECREASE, STAY_SAME]}
          correctIndex={vegaCorrectIndex}
          explanation={`Vega is ${vega.toFixed(3)} (price change per 1% move in volatility) and is never negative for a standard option — more uncertainty makes both calls and puts more valuable.`}
        />

        <PredictionChallenge
          question="One week passes and nothing else changes. What happens to the option's price?"
          options={[INCREASE, DECREASE, STAY_SAME]}
          correctIndex={thetaCorrectIndex}
          explanation={`Theta is ${theta.toFixed(3)} per day here. Options are a wasting asset: as expiration approaches, there's less time for the stock to move in your favor, so value typically erodes (time decay).`}
        />

        <PredictionChallenge
          question={`Suppose the stock keeps rising well past $${newS.toFixed(0)}. Does each additional $1 move add the same amount of option value as the last $1 move?`}
          options={[
            "Yes, Delta stays fixed as the stock moves",
            "No, Delta itself changes as the stock moves",
            STAY_SAME,
          ]}
          correctIndex={1}
          explanation={`Gamma (${greeks.gamma.value.toFixed(4)} here) measures how fast Delta changes. Since Gamma is nonzero, Delta shifts as ${S.toFixed(0)} moves relative to the strike of $${K.toFixed(0)}, so the option's price is curved (convex), not a straight line.`}
        />
      </div>
    </Card>
  );
}
