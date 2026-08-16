"""One-off script: filter the raw ~1.27GB Kaggle SPY option-chain CSV down to
a shippable curated dataset.

Keeps only near-the-money, short-dated contracts (the ones a beginner-facing
tool would actually show), across every trading day in the source data. Not
part of the running app -- run once to (re)generate data/processed/spy_options_chain.parquet.
"""

import pandas as pd

RAW_PATH = "data/raw/spy_options/spy-daily-eod-options-quotes-2020-2022.zip"
OUT_PATH = "data/processed/spy_options_chain.parquet"

MAX_DTE = 60
MAX_STRIKE_DISTANCE_PCT = 0.10

KEEP_COLUMNS = {
    "[QUOTE_UNIXTIME]": "quote_unixtime",
    " [QUOTE_DATE]": "quote_date",
    " [UNDERLYING_LAST]": "underlying_last",
    " [EXPIRE_DATE]": "expire_date",
    " [DTE]": "dte",
    " [C_IV]": "c_iv",
    " [C_LAST]": "c_last",
    " [C_BID]": "c_bid",
    " [C_ASK]": "c_ask",
    " [C_DELTA]": "c_delta",
    " [C_GAMMA]": "c_gamma",
    " [C_VEGA]": "c_vega",
    " [C_THETA]": "c_theta",
    " [STRIKE]": "strike",
    " [P_IV]": "p_iv",
    " [P_LAST]": "p_last",
    " [P_BID]": "p_bid",
    " [P_ASK]": "p_ask",
    " [P_DELTA]": "p_delta",
    " [P_GAMMA]": "p_gamma",
    " [P_VEGA]": "p_vega",
    " [P_THETA]": "p_theta",
    " [STRIKE_DISTANCE_PCT]": "strike_distance_pct",
}


def main() -> None:
    kept_chunks = []
    total_in = 0
    total_out = 0

    for chunk in pd.read_csv(RAW_PATH, chunksize=500_000, low_memory=False):
        total_in += len(chunk)
        chunk = chunk[list(KEEP_COLUMNS.keys())].rename(columns=KEEP_COLUMNS)

        mask = (chunk["dte"] >= 0) & (chunk["dte"] <= MAX_DTE) & (
            chunk["strike_distance_pct"].abs() <= MAX_STRIKE_DISTANCE_PCT
        )
        filtered = chunk[mask].copy()
        filtered["quote_date"] = filtered["quote_date"].str.strip()
        filtered["expire_date"] = filtered["expire_date"].str.strip()
        total_out += len(filtered)
        kept_chunks.append(filtered)
        print(f"  processed {total_in:,} rows so far, kept {total_out:,}")

    result = pd.concat(kept_chunks, ignore_index=True)

    numeric_columns = [c for c in result.columns if c not in ("quote_date", "expire_date")]
    for col in numeric_columns:
        result[col] = pd.to_numeric(result[col], errors="coerce")

    result.to_parquet(OUT_PATH, index=False)
    print(f"Done. {total_in:,} rows in, {len(result):,} rows out -> {OUT_PATH}")


if __name__ == "__main__":
    main()
