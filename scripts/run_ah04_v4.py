from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from stake.ah04_metrics import probability_displacement

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "ah04" / "sample" / "sample" / "EPL" / "2024-2025"
OUT = ROOT / "data" / "ah04_v4_scan.csv"
BASELINE_MINUTES = 180
MAX_BASELINE_AGE_MINUTES = 10
STALE_MINUTES = 5
PRESSURE_THRESHOLD = 0.015
STRONG_BOOKS = 5
VERY_STRONG_BOOKS = 8

KICKOFFS = {
    2591088: "2025-01-04 15:00", 2591089: "2025-01-04 15:00", 2591090: "2025-01-04 17:30",
    2591091: "2025-01-04 15:00", 2591092: "2025-01-05 14:00", 2591093: "2025-01-05 16:30",
    2591094: "2025-01-04 15:00", 2591095: "2025-01-04 15:00", 2591096: "2025-01-04 12:30",
    2591097: "2025-01-06 20:00", 2591098: "2025-01-15 20:00", 2591099: "2025-01-14 19:30",
    2591100: "2025-01-15 19:30", 2591101: "2025-01-16 19:30", 2591102: "2025-01-15 19:30",
    2591103: "2025-01-14 20:00", 2591104: "2025-01-14 19:30", 2591105: "2025-01-14 19:30",
    2591106: "2025-01-15 19:30", 2591107: "2025-01-16 20:00", 2591108: "2025-01-18 17:30",
    2591109: "2025-01-18 15:00", 2591110: "2025-01-20 20:00", 2591111: "2025-01-19 14:00",
    2591112: "2025-01-19 16:30", 2591113: "2025-01-18 15:00", 2591114: "2025-01-19 14:00",
    2591115: "2025-01-18 12:30", 2591116: "2025-01-18 15:00", 2591117: "2025-01-18 15:00",
}


def fixture_id(path: Path) -> int:
    match = re.search(r"match_(\d+)\.csv$", path.name)
    if not match:
        raise ValueError(f"Could not parse fixture id from {path.name}")
    return int(match.group(1))


def parse_line(value: object) -> float | None:
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    try:
        if "/" in s:
            a, b = s.split("/", 1)
            return (float(a) + float(b)) / 2
        return float(s)
    except ValueError:
        return None


def read_fixture(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    needed = ["Teams", "Bookmaker", "Home Odds", "Handicap", "Away Odds", "Timestamp"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name} missing columns: {missing}")
    df = df[needed].copy()
    df["timestamp"] = pd.to_datetime(
        df["Timestamp"].astype(str), format="%Y%m%d%H%M%S", utc=True, errors="coerce"
    )
    df["home_price"] = pd.to_numeric(df["Home Odds"], errors="coerce")
    df["away_price"] = pd.to_numeric(df["Away Odds"], errors="coerce")
    df["line"] = df["Handicap"].map(parse_line)
    # Source rows are newest-to-oldest; temporal selection must be ascending.
    return (
        df.dropna(subset=["timestamp", "home_price", "away_price", "line"])
        .sort_values(["Bookmaker", "timestamp"], kind="stable")
        .reset_index(drop=True)
    )


def main() -> None:
    rows = []
    print("=== AH-04 V4 — NORMALIZED PROBABILITY PRE-KICKOFF SCAN ===")
    print(
        f"Baseline: T-{BASELINE_MINUTES}m | max age: {MAX_BASELINE_AGE_MINUTES}m | "
        f"stale: {STALE_MINUTES}m | threshold: {PRESSURE_THRESHOLD:.3f}"
    )

    for path in sorted(DATA.glob("round*_match_*.csv")):
        fid = fixture_id(path)
        kickoff = pd.Timestamp(KICKOFFS[fid], tz="UTC")
        raw = read_fixture(path)
        pre = raw[raw["timestamp"] < kickoff].copy()
        books = sorted(pre["Bookmaker"].dropna().unique())
        baseline_time = kickoff - pd.Timedelta(minutes=BASELINE_MINUTES)
        baselines = {}
        for book in books:
            b = pre[(pre["Bookmaker"] == book) & (pre["timestamp"] <= baseline_time)]
            if b.empty:
                continue
            tick = b.iloc[-1]
            age = (baseline_time - tick["timestamp"]).total_seconds() / 60
            if age <= MAX_BASELINE_AGE_MINUTES:
                baselines[book] = tick

        base = {
            "fixture": path.stem,
            "teams": str(pre["Teams"].iloc[0]) if not pre.empty else "",
            "status": "OK" if baselines else "INSUFFICIENT_BASELINE",
            "books_seen": len(books), "books_with_baseline": len(baselines),
            "first_strong": pd.NaT, "first_very_strong": pd.NaT,
            "peak_time": pd.NaT, "peak_books": 0, "peak_direction": "",
            "first_line_change": pd.NaT, "pressure_to_line_min": None,
            "reversal_time": pd.NaT, "line_change_minutes": 0,
            "event_class": "INSUFFICIENT_COVERAGE",
        }
        if not baselines:
            rows.append(base)
            continue

        start = kickoff - pd.Timedelta(minutes=BASELINE_MINUTES)
        end = kickoff - pd.Timedelta(seconds=1)
        grid = pd.date_range(start.floor("min"), end.floor("min"), freq="min", tz="UTC")
        peak_count = 0
        peak_dir = ""
        peak_time = pd.NaT
        first_pressure = None
        first_line = None
        reversal = None
        line_minutes = []

        for minute in grid:
            counts = {"HOME": 0, "AWAY": 0}
            current_any = {}
            for book, b in baselines.items():
                ticks = pre[(pre["Bookmaker"] == book) & (pre["timestamp"] <= minute)]
                if ticks.empty:
                    continue
                tick = ticks.iloc[-1]
                age = (minute - tick["timestamp"]).total_seconds() / 60
                if age < 0 or age > STALE_MINUTES:
                    continue
                obs = probability_displacement(
                    float(b["home_price"]), float(b["away_price"]),
                    float(tick["home_price"]), float(tick["away_price"]),
                )
                if obs.home_delta >= PRESSURE_THRESHOLD and obs.away_delta <= -PRESSURE_THRESHOLD:
                    counts["HOME"] += 1
                elif obs.away_delta >= PRESSURE_THRESHOLD and obs.home_delta <= -PRESSURE_THRESHOLD:
                    counts["AWAY"] += 1
                current_any[book] = tick

            direction = "HOME" if counts["HOME"] >= counts["AWAY"] else "AWAY"
            peak = counts[direction]
            if peak > peak_count:
                peak_count, peak_dir, peak_time = peak, direction, minute
            if peak >= STRONG_BOOKS and first_pressure is None:
                first_pressure = minute
            if peak >= VERY_STRONG_BOOKS and pd.isna(base["first_very_strong"]):
                base["first_very_strong"] = minute

            line_changed = 0
            for book, tick in current_any.items():
                b = baselines[book]
                if abs(float(tick["line"]) - float(b["line"])) > 1e-9:
                    line_changed += 1
            if line_changed:
                line_minutes.append(minute)
                if first_line is None:
                    first_line = minute

            if first_pressure is not None and reversal is None:
                if (direction == "HOME" and counts["AWAY"] >= STRONG_BOOKS) or (
                    direction == "AWAY" and counts["HOME"] >= STRONG_BOOKS
                ):
                    reversal = minute

        base["first_strong"] = first_pressure if first_pressure is not None else pd.NaT
        base["peak_time"] = peak_time
        base["peak_books"] = peak_count
        base["peak_direction"] = peak_dir
        base["first_line_change"] = first_line if first_line is not None else pd.NaT
        base["pressure_to_line_min"] = (
            (first_line - first_pressure).total_seconds() / 60
            if first_pressure is not None and first_line is not None else None
        )
        base["reversal_time"] = reversal if reversal is not None else pd.NaT
        base["line_change_minutes"] = len(set(line_minutes))
        if peak_count >= VERY_STRONG_BOOKS:
            base["event_class"] = "VERY_STRONG_PRESSURE"
        elif peak_count >= STRONG_BOOKS and first_line is not None and reversal is not None:
            base["event_class"] = "PRESSURE_LINE_REVERSAL"
        elif peak_count >= STRONG_BOOKS and first_line is not None:
            base["event_class"] = "PRESSURE_LINE"
        elif peak_count >= STRONG_BOOKS:
            base["event_class"] = "PRESSURE_ONLY"
        elif first_line is not None:
            base["event_class"] = "LINE_ONLY"
        else:
            base["event_class"] = "NO_STRONG_EVENT"
        rows.append(base)

    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False)
    print(result[[
        "fixture", "status", "books_seen", "books_with_baseline", "first_strong",
        "peak_time", "peak_books", "peak_direction", "first_line_change",
        "pressure_to_line_min", "reversal_time", "event_class",
    ]].to_string(index=False))
    print("\n=== SUMMARY ===")
    print("Fixtures:", len(result))
    print("Valid:", int((result.status == "OK").sum()))
    print("5+ synchronized pressure:", int((result.peak_books >= STRONG_BOOKS).sum()))
    print("8+ synchronized pressure:", int((result.peak_books >= VERY_STRONG_BOOKS).sum()))
    print("Line movement:", int(result.first_line_change.notna().sum()))
    print("Reversal detected:", int(result.reversal_time.notna().sum()))
    print("\n=== EVENT CLASSES ===")
    print(result["event_class"].value_counts(dropna=False).to_string())
    print("\nSaved:", OUT)


if __name__ == "__main__":
    main()
