from __future__ import annotations

import pandas as pd
import pytest

from stake.ou_disagreement import evaluate_ou_disagreement


def _frame() -> pd.DataFrame:
    rows = []
    # Give both teams enough prior history while keeping the fixture sequence
    # deterministic. The final fixture is the observation under test.
    fixtures = [
        ("2021-08-01", "A", "B", 3, 0, 2.0, 1.9),
        ("2021-08-08", "B", "A", 0, 0, 2.0, 1.9),
        ("2021-08-15", "A", "B", 2, 1, 2.0, 1.9),
        ("2021-08-22", "B", "A", 0, 1, 2.0, 1.9),
        ("2021-08-29", "A", "B", 3, 0, 2.0, 1.9),
        ("2021-09-05", "B", "A", 0, 0, 2.0, 1.9),
    ]
    for date, home, away, fhg, fag, over, under in fixtures:
        rows.append(
            {
                "Date": pd.Timestamp(date),
                "Time": "15:00",
                "HomeTeam": home,
                "AwayTeam": away,
                "FTHG": fhg,
                "FTAG": fag,
                "FTR": "H" if fhg > fag else "A" if fag > fhg else "D",
                "Avg>2.5": over,
                "Avg<2.5": under,
            }
        )
    return pd.DataFrame(rows)


def test_disagreement_probe_returns_fixed_buckets():
    result = evaluate_ou_disagreement(_frame(), window=2)
    assert result.observations > 0
    assert all(bucket.observations > 0 for bucket in result.buckets)
    assert all(0 <= bucket.win_rate <= 1 for bucket in result.buckets)


def test_disagreement_rejects_invalid_window():
    with pytest.raises(ValueError):
        evaluate_ou_disagreement(_frame(), window=0)
