from __future__ import annotations

import pandas as pd
import pytest

from stake.ah_backtest import _ah_distribution, _expected_ah_settlement, evaluate_ah_walk_forward


def _frame() -> pd.DataFrame:
    rows = []
    fixtures = [
        ("2021-08-01", "A", "B", 2, 0, 0.0, 1.90, 1.90),
        ("2021-08-08", "B", "A", 0, 1, 0.0, 1.90, 1.90),
        ("2021-08-15", "A", "B", 3, 0, -0.5, 1.90, 1.90),
        ("2021-08-22", "B", "A", 1, 1, 0.5, 1.90, 1.90),
        ("2021-08-29", "A", "B", 1, 0, -0.25, 1.90, 1.90),
        ("2021-09-05", "B", "A", 0, 2, 0.25, 1.90, 1.90),
        ("2021-09-12", "A", "B", 2, 1, 0.0, 1.90, 1.90),
        ("2021-09-19", "B", "A", 0, 1, 0.0, 1.90, 1.90),
    ]
    for date, home, away, fhg, fag, line, home_odds, away_odds in fixtures:
        rows.append(
            {
                "Date": pd.Timestamp(date),
                "Time": "15:00",
                "HomeTeam": home,
                "AwayTeam": away,
                "FTHG": fhg,
                "FTAG": fag,
                "FTR": "H" if fhg > fag else "A" if fag > fhg else "D",
                "AHh": line,
                "AvgAHH": home_odds,
                "AvgAHA": away_odds,
                "Avg>2.5": 2.0,
                "Avg<2.5": 1.9,
            }
        )
    return pd.DataFrame(rows)


def test_expected_ah_settlement_respects_push_and_quarter_line():
    assert _expected_ah_settlement(0.8, 0.8, 0.0) == pytest.approx(0.0, abs=0.05)
    assert _expected_ah_settlement(1.5, 0.5, -0.25) > 0


def test_distribution_probabilities_sum_to_truncated_poisson_mass():
    result = _ah_distribution(1.2, 0.9, -0.25)
    total = (
        result.full_win
        + result.half_win
        + result.push
        + result.half_loss
        + result.full_loss
    )
    assert 0.999 < total <= 1.0
    assert result.positive_settlement_probability == pytest.approx(
        result.full_win + result.half_win
    )
    assert result.expected_settlement == pytest.approx(
        result.full_win + 0.5 * result.half_win - 0.5 * result.half_loss - result.full_loss
    )


def test_fair_odds_are_defined_when_positive_settlement_mass_exists():
    result = _ah_distribution(1.5, 0.8, -0.25)
    assert result.fair_decimal_odds is not None
    assert result.fair_decimal_odds > 1.0


def test_ah_walk_forward_returns_fixed_buckets():
    result = evaluate_ah_walk_forward(_frame(), window=2)
    assert result.observations > 0
    assert len(result.buckets) == 4
    assert sum(bucket.observations for bucket in result.buckets) == result.observations
    assert all(bucket.observations >= 0 for bucket in result.buckets)


def test_ah_rejects_invalid_window():
    with pytest.raises(ValueError):
        evaluate_ah_walk_forward(_frame(), window=0)
