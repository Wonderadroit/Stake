from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from stake.ah04_metrics import probability_displacement

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "ah04" / "sample" / "sample" / "EPL" / "2024-2025"
OUT = ROOT / "data" / "ah04_v5_scan.csv"

# AH-04 V5 deliberately measures local market events rather than cumulative
# displacement from one T-180 state. Thresholds are measurement parameters,
# not betting/selection thresholds and are not tuned on individual fixtures.
BASELINE_MINUTES = 180
MAX_BASELINE_AGE_MINUTES = 30
STALE_MINUTES = 5
PRESSURE_THRESHOLD = 0.015
STRONG_BOOKS = 5
VERY_STRONG_BOOKS = 8
LOCAL_WINDOWS = (1, 3, 5, 10)

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
    return (
        df.dropna(subset=["timestamp", "home_price", "away_price", "line"])
        .sort_values(["Bookmaker", "timestamp"], kind="stable")
        .reset_index(drop=True)
    )


def latest_tick_at_or_before(group: pd.DataFrame, timestamp: pd.Timestamp) -> pd.Series | None:
    ticks = group[group["timestamp"] <= timestamp]
    if ticks.empty:
        return None
    return ticks.iloc[-1]


def local_observation(group: pd.DataFrame, timestamp: pd.Timestamp, stale_minutes: int) -> pd.Series | None:
    tick = latest_tick_at_or_before(group, timestamp)
    if tick is None:
        return None
    age = (timestamp - tick["timestamp"]).total_seconds() / 60
    if age < 0 or age > stale_minutes:
        return None
    return tick


def pressure_direction(
    baseline: pd.Series, current: pd.Series, threshold: float = PRESSURE_THRESHOLD
) -> str:
    obs = probability_displacement(
        float(baseline["home_price"]), float(baseline["away_price"]),
        float(current["home_price"]), float(current["away_price"]),
    )
    if obs.home_delta >= threshold and obs.away_delta <= -threshold:
        return "HOME"
    if obs.away_delta >= threshold and obs.home_delta <= -threshold:
        return "AWAY"
    return "NONE"


def local_direction(group: pd.DataFrame, timestamp: pd.Timestamp, minutes: int) -> str:
    current = local_observation(group, timestamp, STALE_MINUTES)
    previous = local_observation(group, timestamp - pd.Timedelta(minutes=minutes), STALE_MINUTES)
    if current is None or previous is None:
        return "NONE"
    return pressure_direction(previous, current)


def line_changed(group: pd.DataFrame, baseline: pd.Series, timestamp: pd.Timestamp) -> bool:
    current = local_observation(group, timestamp, STALE_MINUTES)
    if current is None:
        return False
    return abs(float(current["line"]) - float(baseline["line"])) > 1e-9


def main() -> None:
    rows: list[dict[str, object]] = []
    print("=== AH-04 V5 — LOCAL PROBABILITY MOVEMENT / EVENT-SEQUENCE SCAN ===")
    print(
        f"Baseline target: T-{BASELINE_MINUTES}m | max baseline age: {MAX_BASELINE_AGE_MINUTES}m | "
        f"stale: {STALE_MINUTES}m | pressure threshold: {PRESSURE_THRESHOLD:.3f} | "
        f"local windows: {','.join(map(str, LOCAL_WINDOWS))}m"
    )

    for path in sorted(DATA.glob("round*_match_*.csv")):
        fid = fixture_id(path)
        kickoff = pd.Timestamp(KICKOFFS[fid], tz="UTC")
        raw = read_fixture(path)
        pre = raw[raw["timestamp"] < kickoff].copy()
        books = sorted(pre["Bookmaker"].dropna().unique())
        baseline_target = kickoff - pd.Timedelta(minutes=BASELINE_MINUTES)
        grouped = {book: g for book, g in pre.groupby("Bookmaker", sort=False)}
        baselines: dict[str, pd.Series] = {}
        baseline_ages: list[float] = []

        for book, group in grouped.items():
            tick = latest_tick_at_or_before(group, baseline_target)
            if tick is None:
                continue
            age = (baseline_target - tick["timestamp"]).total_seconds() / 60
            if age <= MAX_BASELINE_AGE_MINUTES:
                baselines[book] = tick
                baseline_ages.append(age)

        row: dict[str, object] = {
            "fixture": path.stem,
            "teams": str(pre["Teams"].iloc[0]) if not pre.empty else "",
            "kickoff": kickoff,
            "status": "OK" if baselines else "INSUFFICIENT_BASELINE",
            "books_seen": len(books),
            "books_with_baseline": len(baselines),
            "baseline_age_min": min(baseline_ages) if baseline_ages else None,
            "baseline_age_median": float(pd.Series(baseline_ages).median()) if baseline_ages else None,
            "first_strong_1m": pd.NaT,
            "first_strong_3m": pd.NaT,
            "first_strong_5m": pd.NaT,
            "first_strong_10m": pd.NaT,
            "peak_time_1m": pd.NaT,
            "peak_books_1m": 0,
            "peak_direction_1m": "",
            "first_line_change": pd.NaT,
            "pressure_before_line": False,
            "line_before_pressure": False,
            "simultaneous": False,
            "reversal_after_pressure": pd.NaT,
            "event_class": "INSUFFICIENT_COVERAGE",
        }
        if not baselines:
            rows.append(row)
            continue

        start = kickoff - pd.Timedelta(minutes=30)
        end = kickoff - pd.Timedelta(seconds=1)
        grid = pd.date_range(start.floor("min"), end.floor("min"), freq="min", tz="UTC")

        first_pressure: dict[int, pd.Timestamp | None] = {m: None for m in LOCAL_WINDOWS}
        peak_1m = 0
        peak_1m_time = pd.NaT
        peak_1m_direction = ""
        first_line: pd.Timestamp | None = None
        reversal: pd.Timestamp | None = None
        first_pressure_dir: str | None = None
        line_times: list[pd.Timestamp] = []

        for minute in grid:
            counts = {"HOME": 0, "AWAY": 0}
            for book, baseline in baselines.items():
                group = grouped[book]
                for window in LOCAL_WINDOWS:
                    direction = local_direction(group, minute, window)
                    if direction in counts and window == 1:
                        counts[direction] += 1

            direction = "HOME" if counts["HOME"] >= counts["AWAY"] else "AWAY"
            peak = counts[direction]
            if peak > peak_1m:
                peak_1m = peak
                peak_1m_time = minute
                peak_1m_direction = direction
            if peak >= STRONG_BOOKS and first_pressure[1] is None:
                first_pressure[1] = minute
                first_pressure_dir = direction
            # Record first strong event for the wider local windows independently.
            for window in (3, 5, 10):
                qualifying = 0
                qualifying_direction = "HOME" if counts["HOME"] >= counts["AWAY"] else "AWAY"
                for book in baselines:
                    d = local_direction(grouped[book], minute, window)
                    if d == qualifying_direction:
                        qualifying += 1
                if qualifying >= STRONG_BOOKS and first_pressure[window] is None:
                    first_pressure[window] = minute

            changed_books = [book for book, baseline in baselines.items() if line_changed(grouped[book], baseline, minute)]
            if changed_books:
                line_times.append(minute)
                if first_line is None:
                    first_line = minute

            if first_pressure_dir and reversal is None:
                opposite = "AWAY" if first_pressure_dir == "HOME" else "HOME"
                if counts[opposite] >= STRONG_BOOKS:
                    reversal = minute

        for window in LOCAL_WINDOWS:
            row[f"first_strong_{window}m"] = first_pressure[window] if first_pressure[window] is not None else pd.NaT
        row["peak_time_1m"] = peak_1m_time
        row["peak_books_1m"] = peak_1m
        row["peak_direction_1m"] = peak_1m_direction
        row["first_line_change"] = first_line if first_line is not None else pd.NaT
        row["reversal_after_pressure"] = reversal if reversal is not None else pd.NaT

        if first_pressure[1] is not None and first_line is not None:
            if first_pressure[1] < first_line:
                row["pressure_before_line"] = True
            elif first_line < first_pressure[1]:
                row["line_before_pressure"] = True
            else:
                row["simultaneous"] = True

        if peak_1m >= VERY_STRONG_BOOKS:
            row["event_class"] = "VERY_STRONG_LOCAL_PRESSURE"
        elif peak_1m >= STRONG_BOOKS and row["pressure_before_line"] and reversal is not None:
            row["event_class"] = "PRESSURE_BEFORE_LINE_REVERSAL"
        elif peak_1m >= STRONG_BOOKS and row["pressure_before_line"]:
            row["event_class"] = "PRESSURE_BEFORE_LINE"
        elif peak_1m >= STRONG_BOOKS and row["line_before_pressure"]:
            row["event_class"] = "LINE_BEFORE_PRESSURE"
        elif peak_1m >= STRONG_BOOKS:
            row["event_class"] = "LOCAL_PRESSURE_ONLY"
        elif first_line is not None:
            row["event_class"] = "LINE_ONLY"
        else:
            row["event_class"] = "NO_STRONG_EVENT"
        rows.append(row)

    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False)
    cols = [
        "fixture", "status", "books_seen", "books_with_baseline", "baseline_age_median",
        "first_strong_1m", "first_strong_3m", "first_strong_5m", "first_strong_10m",
        "peak_time_1m", "peak_books_1m", "peak_direction_1m", "first_line_change",
        "pressure_before_line", "line_before_pressure", "simultaneous", "reversal_after_pressure",
        "event_class",
    ]
    print(result[cols].to_string(index=False))
    print("\n=== SUMMARY ===")
    print("Fixtures:", len(result))
    print("Valid:", int((result.status == "OK").sum()))
    print("5+ local 1m pressure:", int((result.peak_books_1m >= STRONG_BOOKS).sum()))
    print("8+ local 1m pressure:", int((result.peak_books_1m >= VERY_STRONG_BOOKS).sum()))
    print("Line movement:", int(result.first_line_change.notna().sum()))
    print("Pressure before line:", int(result.pressure_before_line.sum()))
    print("Line before pressure:", int(result.line_before_pressure.sum()))
    print("Reversal after pressure:", int(result.reversal_after_pressure.notna().sum()))
    print("\n=== EVENT CLASSES ===")
    print(result["event_class"].value_counts(dropna=False).to_string())
    print("\nSaved:", OUT)


if __name__ == "__main__":
    main()
