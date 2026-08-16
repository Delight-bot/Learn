import type {
  BlackScholesResponse,
  GreeksResponse,
  MonteCarloResponse,
  OptionRequest,
  ScenarioName,
  ScenarioResponse,
} from "../types/option";
import type {
  ModelVsMarketRequest,
  ModelVsMarketResponse,
  OptionChainResponse,
  PriceHistoryResponse,
  RealizedVolatilityResponse,
} from "../types/historical";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${path} failed: ${res.status} ${detail}`);
  }
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function get<T>(path: string, params: Record<string, string | number>): Promise<T> {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)]))
  ).toString();
  return request<T>(`${path}?${qs}`);
}

export function fetchBlackScholes(req: OptionRequest) {
  return post<BlackScholesResponse>("/api/black-scholes", req);
}

export function fetchGreeks(req: OptionRequest) {
  return post<GreeksResponse>("/api/greeks", req);
}

export function fetchMonteCarlo(req: OptionRequest, n_simulations: number) {
  return post<MonteCarloResponse>("/api/monte-carlo", { ...req, n_simulations });
}

export function fetchScenario(base: OptionRequest, scenario: ScenarioName) {
  return post<ScenarioResponse>("/api/scenario", { base, scenario });
}

export function fetchPriceHistory(start?: string, end?: string) {
  const params: Record<string, string> = {};
  if (start) params.start = start;
  if (end) params.end = end;
  return get<PriceHistoryResponse>("/api/historical/price-history", params);
}

export function fetchRealizedVolatility(date: string, windowDays: number) {
  return get<RealizedVolatilityResponse>("/api/historical/realized-volatility", {
    date,
    window_days: windowDays,
  });
}

export function fetchQuoteDates() {
  return request<string[]>("/api/historical/quote-dates");
}

export function fetchExpirations(quoteDate: string) {
  return get<string[]>("/api/historical/expirations", { quote_date: quoteDate });
}

export function fetchOptionChain(quoteDate: string, expireDate: string) {
  return get<OptionChainResponse>("/api/historical/option-chain", {
    quote_date: quoteDate,
    expire_date: expireDate,
  });
}

export function fetchModelVsMarket(req: ModelVsMarketRequest) {
  return post<ModelVsMarketResponse>("/api/historical/compare", req);
}
