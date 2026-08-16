import type { OptionType } from "./option";

export interface PricePoint {
  date: string;
  close: number;
}

export interface PriceHistoryResponse {
  start: string;
  end: string;
  points: PricePoint[];
}

export interface RealizedVolatilityResponse {
  date: string;
  window_days: number;
  annualized_volatility: number;
  spy_close: number;
}

export interface OptionChainRow {
  strike: number;
  dte: number;
  underlying_last: number;
  c_last: number | null;
  c_bid: number | null;
  c_ask: number | null;
  c_iv: number | null;
  p_last: number | null;
  p_bid: number | null;
  p_ask: number | null;
  p_iv: number | null;
}

export interface OptionChainResponse {
  quote_date: string;
  expire_date: string;
  underlying_last: number;
  rows: OptionChainRow[];
}

export interface ModelVsMarketRequest {
  quote_date: string;
  expire_date: string;
  strike: number;
  option_type: OptionType;
  r?: number;
  realized_vol_window_days?: number;
}

export interface ModelVsMarketResponse {
  quote_date: string;
  expire_date: string;
  strike: number;
  option_type: OptionType;
  dte: number;
  underlying_last: number;

  market_last: number | null;
  market_bid: number | null;
  market_ask: number | null;
  market_mid: number | null;
  market_implied_vol: number | null;

  model_price_using_market_iv: number | null;
  realized_volatility: number;
  model_price_using_realized_vol: number;

  market_vs_model_iv_diff: number | null;
  market_vs_model_realized_vol_diff: number | null;
}
