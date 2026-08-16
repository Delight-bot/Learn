export type OptionType = "call" | "put";

export interface OptionRequest {
  S: number;
  K: number;
  days_to_expiration: number;
  sigma: number; // decimal, e.g. 0.20 for 20%
  r: number; // decimal, e.g. 0.045 for 4.5%
  option_type: OptionType;
}

export interface BlackScholesResponse {
  price: number;
  d1: number;
  d2: number;
}

export interface GreekExplanation {
  value: number;
  explanation: string;
}

export interface GreeksResponse {
  delta: GreekExplanation;
  gamma: GreekExplanation;
  vega: GreekExplanation;
  theta: GreekExplanation;
}

export interface ConvergencePoint {
  n_simulations: number;
  price: number;
}

export interface MonteCarloResponse {
  black_scholes_price: number;
  monte_carlo_price: number;
  absolute_difference: number;
  std_error: number;
  n_simulations: number;
  sample_paths: number[][];
  time_grid: number[];
  convergence: ConvergencePoint[];
}

export type ScenarioName =
  | "stock_up_5"
  | "stock_down_5"
  | "vol_up_5"
  | "time_passes_1w";

export interface ScenarioResponse {
  label: string;
  original_price: number;
  new_price: number;
  difference: number;
  greek_used: string;
  greek_value: number;
  greek_estimated_difference: number;
}
