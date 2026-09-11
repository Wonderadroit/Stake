from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from stake.ah04_v5 import event_order, line_changed, local_move

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "ah04" / "sample" / "sample" / "EPL" / "2024-2025"
OUT = ROOT / "data" / "ah04_v5_1_scan.csv"
PRESSURE_THRESHOLD = 0.015
STRONG_BOOKS = 5
VERY_STRONG_BOOKS = 8
MAX_GAP_MINUTES = 5
LOCAL_WINDOWS = (1, 3, 5, 10)

KICKOFFS = {
    2591088:"2025-01-04 15:00",2591089:"2025-01-04 15:00",2591090:"2025-01-04 17:30",2591091:"2025-01-04 15:00",2591092:"2025-01-05 14:00",2591093:"2025-01-05 16:30",2591094:"2025-01-04 15:00",2591095:"2025-01-04 15:00",2591096:"2025-01-04 12:30",2591097:"2025-01-06 20:00",2591098:"2025-01-15 20:00",2591099:"2025-01-14 19:30",2591100:"2025-01-15 19:30",2591101:"2025-01-16 19:30",2591102:"2025-01-15 19:30",2591103:"2025-01-14 20:00",2591104:"2025-01-14 19:30",2591105:"2025-01-14 19:30",2591106:"2025-01-15 19:30",2591107:"2025-01-16 20:00",2591108:"2025-01-18 17:30",2591109:"2025-01-18 15:00",2591110:"2025-01-20 20:00",2591111:"2025-01-19 14:00",2591112:"2025-01-19 16:30",2591113:"2025-01-18 15:00",2591114:"2025-01-19 14:00",2591115:"2025-01-18 12:30",2591116:"2025-01-18 15:00",2591117:"2025-01-18 15:00",
}


def fixture_id(path: Path) -> int:
    m = re.search(r"match_(\d+)\.csv$", path.name)
    if not m:
        raise ValueError(f"Could not parse fixture id from {path.name}")
    return int(m.group(1))


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
    df["timestamp"] = pd.to_datetime(df["Timestamp"].astype(str), format="%Y%m%d%H%M%S", utc=True, errors="coerce")
    df["home_price"] = pd.to_numeric(df["Home Odds"], errors="coerce")
    df["away_price"] = pd.to_numeric(df["Away Odds"], errors="coerce")
    df["line"] = df["Handicap"].map(parse_line)
    return df.dropna(subset=["timestamp","home_price","away_price","line"]).sort_values(["Bookmaker","timestamp"], kind="stable").reset_index(drop=True)


def first_local_pressure(group: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, window: int) -> pd.Timestamp | None:
    previous = None
    for _, current in group[(group.timestamp >= start) & (group.timestamp < end)].iterrows():
        if previous is not None:
            elapsed = (current.timestamp - previous.timestamp).total_seconds() / 60
            if elapsed <= window and elapsed <= MAX_GAP_MINUTES:
                move = local_move(previous, current, PRESSURE_THRESHOLD)
                if move.direction != "NONE":
                    return current.timestamp
        previous = current
    return None


def pressure_counts_at(ticks: dict[str, pd.DataFrame], timestamp: pd.Timestamp, window: int) -> dict[str, int]:
    counts = {"HOME": 0, "AWAY": 0}
    for group in ticks.values():
        prior = group[group.timestamp < timestamp]
        current = group[group.timestamp <= timestamp]
        if prior.empty or current.empty:
            continue
        p = prior.iloc[-1]
        c = current.iloc[-1]
        elapsed = (c.timestamp - p.timestamp).total_seconds() / 60
        if elapsed <= 0 or elapsed > window or elapsed > MAX_GAP_MINUTES:
            continue
        move = local_move(p, c, PRESSURE_THRESHOLD)
        if move.direction in counts:
            counts[move.direction] += 1
    return counts


def main() -> None:
    rows = []
    print("=== AH-04 V5.1 — ACTUAL-TICK LOCAL EVENT SCAN ===")
    print(f"threshold={PRESSURE_THRESHOLD:.3f} | strong={STRONG_BOOKS} | very_strong={VERY_STRONG_BOOKS} | max_gap={MAX_GAP_MINUTES}m")
    print("Local pressure uses every bookmaker with consecutive pre-kickoff ticks; T-180 baseline is NOT required for event detection.")

    for path in sorted(DATA.glob("round*_match_*.csv")):
        fid = fixture_id(path)
        kickoff = pd.Timestamp(KICKOFFS[fid], tz="UTC")
        pre = read_fixture(path)
        pre = pre[pre.timestamp < kickoff]
        groups = {book: g.reset_index(drop=True) for book, g in pre.groupby("Bookmaker", sort=False)}
        start = kickoff - pd.Timedelta(minutes=30)
        end = kickoff
        row = {"fixture": path.stem, "teams": str(pre.Teams.iloc[0]) if not pre.empty else "", "kickoff": kickoff,
               "books_seen": len(groups), "first_strong_1m": pd.NaT, "first_strong_3m": pd.NaT,
               "first_strong_5m": pd.NaT, "first_strong_10m": pd.NaT, "peak_books_1m": 0,
               "peak_time_1m": pd.NaT, "peak_direction_1m": "", "first_line_change": pd.NaT,
               "pressure_before_line": False, "line_before_pressure": False, "simultaneous": False,
               "reversal_after_pressure": pd.NaT, "event_class": "NO_STRONG_EVENT"}

        # First strong local pressure is measured independently at each window.
        for window in LOCAL_WINDOWS:
            candidates = [first_local_pressure(g, start, end, window) for g in groups.values()]
            candidates = [x for x in candidates if x is not None]
            if candidates:
                # A single-book first tick is not an event. Reconstruct minute bins and require concurrence.
                times = pd.DatetimeIndex(candidates).floor("min").unique()
                qualifying = []
                for t in times:
                    counts = pressure_counts_at(groups, t + pd.Timedelta(minutes=1), window)
                    if max(counts.values()) >= STRONG_BOOKS:
                        qualifying.append(t)
                if qualifying:
                    row[f"first_strong_{window}m"] = min(qualifying)

        # Dense minute grid is only an aggregation layer; pressure itself comes from actual ticks.
        pressure_events = []
        for minute in pd.date_range(start.floor("min"), (kickoff - pd.Timedelta(seconds=1)).floor("min"), freq="min", tz="UTC"):
            counts = pressure_counts_at(groups, minute + pd.Timedelta(minutes=1), 1)
            direction = "HOME" if counts["HOME"] >= counts["AWAY"] else "AWAY"
            count = counts[direction]
            pressure_events.append((minute, count, direction))
        if pressure_events:
            peak_time, peak_count, peak_direction = max(pressure_events, key=lambda x: x[1])
            row["peak_time_1m"], row["peak_books_1m"], row["peak_direction_1m"] = peak_time, peak_count, peak_direction

        # Local line changes: compare each actual tick with that bookmaker's immediately prior tick.
        line_times = []
        for group in groups.values():
            recent = group[(group.timestamp >= start) & (group.timestamp < end)]
            for i in range(1, len(recent)):
                prev, cur = recent.iloc[i - 1], recent.iloc[i]
                if line_changed(prev, cur):
                    line_times.append(cur.timestamp)
        first_line = min(line_times) if line_times else None
        row["first_line_change"] = first_line if first_line is not None else pd.NaT

        strong_1m = row["first_strong_1m"]
        if pd.notna(strong_1m) and first_line is not None:
            row["pressure_before_line"] = strong_1m < first_line
            row["line_before_pressure"] = first_line < strong_1m
            row["simultaneous"] = first_line == strong_1m

        if row["peak_books_1m"] >= VERY_STRONG_BOOKS:
            row["event_class"] = "VERY_STRONG_LOCAL_PRESSURE"
        elif row["peak_books_1m"] >= STRONG_BOOKS and row["pressure_before_line"]:
            row["event_class"] = "PRESSURE_BEFORE_LINE"
        elif row["peak_books_1m"] >= STRONG_BOOKS and row["line_before_pressure"]:
            row["event_class"] = "LINE_BEFORE_PRESSURE"
        elif row["peak_books_1m"] >= STRONG_BOOKS:
            row["event_class"] = "LOCAL_PRESSURE_ONLY"
        elif first_line is not None:
            row["event_class"] = "LINE_ONLY"
        rows.append(row)

    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False)
    print(result.to_string(index=False))
    print("\n=== SUMMARY ===")
    print("Fixtures:", len(result))
    print("5+ synchronized local pressure:", int((result.peak_books_1m >= STRONG_BOOKS).sum()))
    print("8+ synchronized local pressure:", int((result.peak_books_1m >= VERY_STRONG_BOOKS).sum()))
    print("Line movement:", int(result.first_line_change.notna().sum()))
    print("Pressure before line:", int(result.pressure_before_line.sum()))
    print("Line before pressure:", int(result.line_before_pressure.sum()))
    print("\n=== EVENT CLASSES ===")
    print(result.event_class.value_counts().to_string())
    print("\nSaved:", OUT)


if __name__ == "__main__":
    main()
