from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
AH_COLUMNS = {"AHh", "AvgAHH", "AvgAHA"}
OU_COLUMNS = {"Avg>2.5", "Avg<2.5"}


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
    return frame.sort_values(["Date", "Time"], na_position="last").reset_index(drop=True)


def load_seasons(paths: list[str | Path]) -> pd.DataFrame:
    """Load and combine historical season CSVs in chronological order."""
    if not paths:
        raise ValueError("At least one season path is required")

    frames: list[pd.DataFrame] = []
    for path in paths:
        frame = load_match_csv(path)
        frame["SeasonSource"] = Path(path).stem
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    return combined.sort_values(["Date", "Time"], na_position="last").reset_index(drop=True)


def chronological_split(
    frame: pd.DataFrame, test_fraction: float = 0.2
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split chronologically; never shuffle historical matches."""
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    ordered = frame.sort_values("Date").reset_index(drop=True)
    cut = max(1, int(len(ordered) * (1 - test_fraction)))
    if cut >= len(ordered):
        raise ValueError("Dataset is too small for the requested split")
    return ordered.iloc[:cut].copy(), ordered.iloc[cut:].copy()


def validate_market_columns(frame: pd.DataFrame) -> None:
    """Require the opening AH and O/U fields used by the first experiment."""
    missing = (AH_COLUMNS | OU_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing market columns: {sorted(missing)}")


def asian_handicap_settlement(home_goals: int, away_goals: int, line: float) -> float:
    """Return settlement for a 1-unit home Asian Handicap bet.

    Returns +1 win, +0.5 half-win, 0 push, -0.5 half-loss, or -1 loss.
    Quarter-goal lines split the stake equally across the two adjacent
    half-goal lines.
    """
    if not isinstance(home_goals, int) or not isinstance(away_goals, int):
        raise TypeError("Goals must be integers")

    # Asian handicap lines may be half- or quarter-goal increments.
    quarter_units = round(line * 4)
    if abs(line * 4 - quarter_units) > 1e-9:
        raise ValueError("Asian Handicap line must use half- or quarter-goal increments")

    # Quarter lines split the stake between the two adjacent half-goal lines.
    if quarter_units % 2:
        lower = line - 0.25
        upper = line + 0.25
        return (
            asian_handicap_settlement(home_goals, away_goals, lower)
            + asian_handicap_settlement(home_goals, away_goals, upper)
        ) / 2

    margin = home_goals - away_goals + line
    if margin > 0:
        return 1.0
    if margin == 0:
        return 0.0
    return -1.0


def over_under_25_settlement(home_goals: int, away_goals: int, over: bool = True) -> float:
    """Return settlement for a 1-unit O/U 2.5 bet."""
    total = home_goals + away_goals
    won = total > 2.5 if over else total < 2.5
    return 1.0 if won else -1.0
