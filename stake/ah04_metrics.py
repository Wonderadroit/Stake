from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class PressureObservation:
    home_probability: float
    away_probability: float
    home_delta: float
    away_delta: float
    direction: str


def asian_implied_probabilities(home_price: float, away_price: float) -> tuple[float, float]:
    """Convert Asian decimal-style payout prices to normalized two-way probabilities."""
    if home_price <= 0 or away_price <= 0:
        raise ValueError("Asian prices must be positive")
    home_raw = 1.0 / (1.0 + home_price)
    away_raw = 1.0 / (1.0 + away_price)
    total = home_raw + away_raw
    return home_raw / total, away_raw / total


def probability_displacement(
    baseline_home_price: float,
    baseline_away_price: float,
    current_home_price: float,
    current_away_price: float,
) -> PressureObservation:
    """Measure normalized market displacement relative to a fixed baseline."""
    base_home, base_away = asian_implied_probabilities(
        baseline_home_price, baseline_away_price
    )
    current_home, current_away = asian_implied_probabilities(
        current_home_price, current_away_price
    )
    home_delta = current_home - base_home
    away_delta = current_away - base_away
    if home_delta >= 0 and away_delta <= 0:
        direction = "HOME"
    elif away_delta >= 0 and home_delta <= 0:
        direction = "AWAY"
    elif abs(home_delta) < 1e-12 and abs(away_delta) < 1e-12:
        direction = "UNCHANGED"
    else:
        direction = "MIXED"
    return PressureObservation(
        home_probability=current_home,
        away_probability=current_away,
        home_delta=home_delta,
        away_delta=away_delta,
        direction=direction,
    )


def classify_probability_pressure(
    home_delta: float,
    away_delta: float,
    threshold: float = 0.015,
) -> str:
    """Classify meaningful two-way probability displacement.

    Threshold is deliberately expressed in probability points and is not a
    betting threshold. It is a measurement parameter for market structure.
    """
    if home_delta >= threshold and away_delta <= -threshold:
        return "HOME_PRESSURE"
    if away_delta >= threshold and home_delta <= -threshold:
        return "AWAY_PRESSURE"
    if max(abs(home_delta), abs(away_delta)) >= threshold:
        return "ASYMMETRIC"
    return "UNCHANGED"


def minute_grid(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range(start=start.floor("min"), end=end.floor("min"), freq="min", tz="UTC")


def finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False
