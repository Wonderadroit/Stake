from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from stake.ah04_metrics import probability_displacement


@dataclass(frozen=True)
class LocalMove:
    direction: str
    home_delta: float
    away_delta: float
    elapsed_minutes: float


def local_move(previous: pd.Series, current: pd.Series, threshold: float = 0.015) -> LocalMove:
    """Measure probability displacement between two consecutive market states."""
    elapsed = (current["timestamp"] - previous["timestamp"]).total_seconds() / 60
    if elapsed <= 0:
        raise ValueError("Current tick must be later than previous tick")
    obs = probability_displacement(
        float(previous["home_price"]),
        float(previous["away_price"]),
        float(current["home_price"]),
        float(current["away_price"]),
    )
    if obs.home_delta >= threshold and obs.away_delta <= -threshold:
        direction = "HOME"
    elif obs.away_delta >= threshold and obs.home_delta <= -threshold:
        direction = "AWAY"
    else:
        direction = "NONE"
    return LocalMove(direction, obs.home_delta, obs.away_delta, elapsed)


def line_changed(previous: pd.Series, current: pd.Series) -> bool:
    return abs(float(current["line"]) - float(previous["line"])) > 1e-9


def event_order(pressure_time: pd.Timestamp | None, line_time: pd.Timestamp | None) -> str:
    """Classify temporal ordering without inventing simultaneity."""
    if pressure_time is None and line_time is None:
        return "NONE"
    if pressure_time is None:
        return "LINE_ONLY"
    if line_time is None:
        return "PRESSURE_ONLY"
    if pressure_time < line_time:
        return "PRESSURE_BEFORE_LINE"
    if line_time < pressure_time:
        return "LINE_BEFORE_PRESSURE"
    return "SIMULTANEOUS"
