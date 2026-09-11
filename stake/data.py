from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}


def load_match_csv(path: str | Path) -> pd.DataFrame:
    """Load a Football-Data-style CSV and validate its minimum schema."""
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    frame = frame.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
    if frame["Date"].isna().any():
        raise ValueError("Invalid match date detected")
    if frame[["HomeTeam", "AwayTeam"]].isna().any().any():
        raise ValueError("Missing team name detected")
    return frame.sort_values("Date").reset_index(drop=True)


def chronological_split(frame: pd.DataFrame, test_fraction: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split chronologically; never shuffle historical matches."""
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    ordered = frame.sort_values("Date").reset_index(drop=True)
    cut = max(1, int(len(ordered) * (1 - test_fraction)))
    if cut >= len(ordered):
        raise ValueError("Dataset is too small for the requested split")
    return ordered.iloc[:cut].copy(), ordered.iloc[cut:].copy()
