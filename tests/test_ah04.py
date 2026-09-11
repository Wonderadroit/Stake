from __future__ import annotations

import pandas as pd
import pytest

from stake.ah04 import build_ah04_windows, normalize_market_ticks


def test_build_window_uses_strict_before_after_and_close() -> None:
    info = pd.DataFrame(
        [
            {
                "fixture_id": "F1",
                "information_timestamp": "2024-01-01T12:00:00Z",
                "event_type": "availability_change",
                "event_value": "player_out",
            }
        ]
    )
    market = pd.DataFrame(
        [
            {"fixture_id": "F1", "market_timestamp": "2024-01-01T11:50:00Z", "handicap_line": -0.5, "home_price": 1.90, "away_price": 1.90},
            {"fixture_id": "F1", "market_timestamp": "2024-01-01T12:10:00Z", "handicap_line": -0.75, "home_price": 1.90, "away_price": 1.90},
            {"fixture_id": "F1", "market_timestamp": "2024-01-01T12:50:00Z", "handicap_line": -0.75, "home_price": 1.85, "away_price": 1.95},
        ]
    )
    fixtures = pd.DataFrame(
        [{"fixture_id": "F1", "kickoff_timestamp": "2024-01-01T13:00:00Z"}]
    )

    result = build_ah04_windows(info, market, fixtures)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["before_timestamp"] == pd.Timestamp("2024-01-01T11:50:00Z")
    assert row["after_timestamp"] == pd.Timestamp("2024-01-01T12:10:00Z")
    assert row["close_timestamp"] == pd.Timestamp("2024-01-01T12:50:00Z")
    assert row["before_line"] == -0.5
    assert row["after_line"] == -0.75
    assert row["close_home_price"] == 1.85


def test_event_at_kickoff_is_rejected() -> None:
    info = pd.DataFrame(
        [{
            "fixture_id": "F1",
            "information_timestamp": "2024-01-01T13:00:00Z",
            "event_type": "availability_change",
            "event_value": "player_out",
        }]
    )
    market = pd.DataFrame(
        [{"fixture_id": "F1", "market_timestamp": "2024-01-01T12:50:00Z", "handicap_line": -0.5, "home_price": 1.9, "away_price": 1.9}]
    )
    fixtures = pd.DataFrame(
        [{"fixture_id": "F1", "kickoff_timestamp": "2024-01-01T13:00:00Z"}]
    )

    result = build_ah04_windows(info, market, fixtures)

    assert result.empty


def test_normalize_market_requires_numeric_line_and_prices() -> None:
    frame = pd.DataFrame(
        [{"fixture_id": "F1", "market_timestamp": "bad", "handicap_line": -0.5, "home_price": 1.9, "away_price": 1.9}]
    )
    with pytest.raises(ValueError, match="invalid timestamps"):
        normalize_market_ticks(frame)
