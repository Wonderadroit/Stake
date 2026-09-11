from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


INFO_COLUMNS = ("fixture_id", "information_timestamp", "event_type", "event_value")
MARKET_COLUMNS = (
    "fixture_id",
    "market_timestamp",
    "handicap_line",
    "home_price",
    "away_price",
)


@dataclass(frozen=True)
class AH04Window:
    fixture_id: str
    information_timestamp: pd.Timestamp
    kickoff_timestamp: pd.Timestamp
    before_timestamp: pd.Timestamp | None
    after_timestamp: pd.Timestamp | None
    close_timestamp: pd.Timestamp | None
    before_line: float | None
    after_line: float | None
    close_line: float | None
    before_home_price: float | None
    after_home_price: float | None
    close_home_price: float | None
    before_away_price: float | None
    after_away_price: float | None
    close_away_price: float | None


def _require(frame: pd.DataFrame, columns: tuple[str, ...], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")


def normalize_information_events(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize timestamped pre-match information events.

    The source must explicitly provide ``information_timestamp``. No event
    time is inferred from news text, kickoff time, or scrape date.
    """
    _require(frame, INFO_COLUMNS, "information events")
    result = frame[list(INFO_COLUMNS)].copy()
    result["information_timestamp"] = pd.to_datetime(
        result["information_timestamp"], utc=True, errors="coerce"
    )
    if result["information_timestamp"].isna().any():
        raise ValueError("information events contain invalid timestamps")
    return result.sort_values(["fixture_id", "information_timestamp"], kind="stable").reset_index(drop=True)


def normalize_market_ticks(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize timestamped AH observations, preserving line and prices."""
    _require(frame, MARKET_COLUMNS, "market ticks")
    result = frame[list(MARKET_COLUMNS)].copy()
    result["market_timestamp"] = pd.to_datetime(
        result["market_timestamp"], utc=True, errors="coerce"
    )
    if result["market_timestamp"].isna().any():
        raise ValueError("market ticks contain invalid timestamps")
    for column in ("handicap_line", "home_price", "away_price"):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    if result[["handicap_line", "home_price", "away_price"]].isna().any().any():
        raise ValueError("market ticks contain invalid line or price values")
    return result.sort_values(["fixture_id", "market_timestamp"], kind="stable").reset_index(drop=True)


def build_ah04_windows(
    information_events: pd.DataFrame,
    market_ticks: pd.DataFrame,
    fixtures: pd.DataFrame,
) -> pd.DataFrame:
    """Build strict before/after/close windows around information events.

    Every selected observation is for the same fixture. ``before`` is the
    latest market tick at or before the information timestamp; ``after`` is
    the earliest tick strictly after it; ``close`` is the latest tick strictly
    before kickoff. Events at or after kickoff are rejected.
    """
    _require(fixtures, ("fixture_id", "kickoff_timestamp"), "fixtures")
    info = normalize_information_events(information_events)
    market = normalize_market_ticks(market_ticks)
    fixture_frame = fixtures[["fixture_id", "kickoff_timestamp"]].copy()
    fixture_frame["kickoff_timestamp"] = pd.to_datetime(
        fixture_frame["kickoff_timestamp"], utc=True, errors="coerce"
    )
    if fixture_frame["kickoff_timestamp"].isna().any():
        raise ValueError("fixtures contain invalid kickoff timestamps")

    rows: list[dict[str, object]] = []
    for event in info.itertuples(index=False):
        fixture_id = str(event.fixture_id)
        fixture_rows = fixture_frame[fixture_frame["fixture_id"].astype(str) == fixture_id]
        if len(fixture_rows) != 1:
            continue
        kickoff = fixture_rows.iloc[0]["kickoff_timestamp"]
        information_time = event.information_timestamp
        if information_time >= kickoff:
            continue

        ticks = market[market["fixture_id"].astype(str) == fixture_id]
        before = ticks[ticks["market_timestamp"] <= information_time].tail(1)
        after = ticks[(ticks["market_timestamp"] > information_time) & (ticks["market_timestamp"] < kickoff)].head(1)
        close = ticks[ticks["market_timestamp"] < kickoff].tail(1)

        def value(frame: pd.DataFrame, column: str):
            return None if frame.empty else frame.iloc[0][column]

        rows.append(
            {
                "fixture_id": fixture_id,
                "event_type": event.event_type,
                "event_value": event.event_value,
                "information_timestamp": information_time,
                "kickoff_timestamp": kickoff,
                "before_timestamp": value(before, "market_timestamp"),
                "after_timestamp": value(after, "market_timestamp"),
                "close_timestamp": value(close, "market_timestamp"),
                "before_line": value(before, "handicap_line"),
                "after_line": value(after, "handicap_line"),
                "close_line": value(close, "handicap_line"),
                "before_home_price": value(before, "home_price"),
                "after_home_price": value(after, "home_price"),
                "close_home_price": value(close, "home_price"),
                "before_away_price": value(before, "away_price"),
                "after_away_price": value(after, "away_price"),
                "close_away_price": value(close, "away_price"),
                "has_before": not before.empty,
                "has_after": not after.empty,
                "has_close": not close.empty,
            }
        )

    return pd.DataFrame(rows)
