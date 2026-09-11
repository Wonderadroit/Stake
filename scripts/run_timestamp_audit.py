"""Audit timestamp resolution and provenance for STAKE historical market data.

This is a data-integrity gate, not a market-signal detector.
It deliberately reports what the raw observations can support and does not
invent bookmaker-event timestamps when only observation timestamps exist.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import math

import pandas as pd


DEFAULT_ROOT = Path("data/raw/ah04/sample/sample/EPL/2024-2025")
TIMESTAMP_CANDIDATES = ("Timestamp", "timestamp", "timestamp_utc", "observation_time")
BOOK_CANDIDATES = ("Bookmaker", "bookmaker", "book")
FIXTURE_CANDIDATES = ("Teams", "teams", "fixture", "Fixture")


def first_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    return next((c for c in candidates if c in df.columns), None)


def parse_timestamp(series: pd.Series) -> pd.Series:
    raw = series.astype(str).str.strip()
    parsed = pd.to_datetime(raw, format="%Y%m%d%H%M%S", utc=True, errors="coerce")
    missing = parsed.isna()
    if missing.any():
        parsed.loc[missing] = pd.to_datetime(
            raw.loc[missing], utc=True, errors="coerce"
        )
    return parsed


def percentile(values: pd.Series, q: float) -> float | None:
    if values.empty:
        return None
    return float(values.quantile(q))


def summarize_frame(df: pd.DataFrame, source: Path) -> dict:
    ts_col = first_column(df, TIMESTAMP_CANDIDATES)
    book_col = first_column(df, BOOK_CANDIDATES)
    fixture_col = first_column(df, FIXTURE_CANDIDATES)
    if not ts_col or not book_col:
        return {
            "file": str(source),
            "status": "SKIP",
            "reason": "missing Timestamp and/or Bookmaker column",
        }

    ts = parse_timestamp(df[ts_col])
    valid = ts.notna()
    work = df.loc[valid, [book_col]].copy()
    work["ts"] = ts.loc[valid]
    work = work.sort_values([book_col, "ts"])

    gaps = work.groupby(book_col)["ts"].diff().dt.total_seconds().dropna()
    positive_gaps = gaps[gaps > 0]

    same_ts_rows = work.duplicated([book_col, "ts"], keep=False)
    same_ts_rate = float(same_ts_rows.mean()) if len(work) else math.nan

    # Cross-book simultaneity is measured on timestamps shared by >=2 books.
    per_ts_books = work.groupby("ts")[book_col].nunique()
    cross_book_same_ts = int((per_ts_books >= 2).sum())
    unique_ts = int(per_ts_books.size)
    cross_book_same_ts_rate = (
        cross_book_same_ts / unique_ts if unique_ts else math.nan
    )

    resolutions = pd.Series(work["ts"].drop_duplicates().sort_values().diff().dt.total_seconds())
    resolutions = resolutions[resolutions > 0]

    horizon_seconds = [5, 15, 30, 60, 180]
    horizon_rows = []
    if not positive_gaps.empty:
        for h in horizon_seconds:
            horizon_rows.append(
                {
                    "seconds": h,
                    "fraction_gaps_le_horizon": float((positive_gaps <= h).mean()),
                }
            )
    else:
        horizon_rows = [{"seconds": h, "fraction_gaps_le_horizon": None} for h in horizon_seconds]

    return {
        "file": str(source),
        "status": "OK",
        "rows": int(len(df)),
        "valid_timestamps": int(valid.sum()),
        "invalid_timestamps": int((~valid).sum()),
        "bookmakers": int(df[book_col].nunique(dropna=True)),
        "fixtures": int(df[fixture_col].nunique(dropna=True)) if fixture_col else None,
        "timestamp_column": ts_col,
        "timestamp_resolution_note": "Observed timestamp only unless source documentation proves event-time semantics",
        "duplicate_same_book_timestamp_rate": same_ts_rate,
        "cross_book_shared_timestamp_rate": cross_book_same_ts_rate,
        "median_inter_observation_gap_seconds": percentile(positive_gaps, 0.50),
        "p95_inter_observation_gap_seconds": percentile(positive_gaps, 0.95),
        "p99_inter_observation_gap_seconds": percentile(positive_gaps, 0.99),
        "median_unique_timestamp_gap_seconds": percentile(resolutions, 0.50),
        "p95_unique_timestamp_gap_seconds": percentile(resolutions, 0.95),
        "horizon_measurability": horizon_rows,
    }


def collect_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(root.rglob("*.csv"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path, default=Path("data/timestamp_audit.json"))
    args = parser.parse_args()

    files = collect_files(args.root)
    if not files:
        raise SystemExit(f"No CSV files found under: {args.root}")

    results = []
    for path in files:
        try:
            df = pd.read_csv(path)
            results.append(summarize_frame(df, path))
        except Exception as exc:  # report bad files without hiding the dataset issue
            results.append({"file": str(path), "status": "ERROR", "reason": repr(exc)})

    ok = [r for r in results if r.get("status") == "OK"]
    output = {
        "audit": "STAKE timestamp/provenance gate",
        "root": str(args.root),
        "files_found": len(files),
        "files_ok": len(ok),
        "files": results,
        "provenance_warning": (
            "A single dataset Timestamp field is treated as observation time. "
            "It is not assumed to be the true bookmaker price-change time."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("=== STAKE TIMESTAMP / PROVENANCE AUDIT ===")
    print(f"files: {len(files)} | readable: {len(ok)}")
    for item in ok:
        print(f"\nFILE: {item['file']}")
        for key in (
            "rows",
            "valid_timestamps",
            "invalid_timestamps",
            "bookmakers",
            "fixtures",
            "duplicate_same_book_timestamp_rate",
            "cross_book_shared_timestamp_rate",
            "median_inter_observation_gap_seconds",
            "p95_inter_observation_gap_seconds",
            "p99_inter_observation_gap_seconds",
            "median_unique_timestamp_gap_seconds",
            "p95_unique_timestamp_gap_seconds",
        ):
            print(f"{key}: {item[key]}")
        print("horizon_measurability:")
        for row in item["horizon_measurability"]:
            print(f"  <= {row['seconds']}s: {row['fraction_gaps_le_horizon']}")

    print(f"\nJSON: {args.output}")
    print("PROVENANCE: observation timestamp unless source documentation proves event-time semantics")


if __name__ == "__main__":
    main()
