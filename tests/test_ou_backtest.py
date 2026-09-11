import pandas as pd
import pytest

from stake.ou_backtest import evaluate_ou_walk_forward


def test_walk_forward_evaluation_uses_opening_market_and_prior_history_only():
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(
                [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                ]
            ),
            "Time": ["15:00"] * 5,
            "HomeTeam": ["A", "B", "A", "B", "A"],
            "AwayTeam": ["B", "A", "B", "A", "B"],
            "FTHG": [1, 0, 3, 0, 100],
            "FTAG": [0, 1, 0, 1, 100],
            "Avg>2.5": [2.0] * 5,
            "Avg<2.5": [2.0] * 5,
        }
    )

    result = evaluate_ou_walk_forward(frame, window=10, min_ev=0.03)

    # Only the first fixture has no prior history. The second fixture can
    # use all-venue fallback history, so four observations are evaluated.
    assert result.observations == 4
    assert 0 <= result.model_brier <= 1
    assert result.market_brier == pytest.approx(0.25)
    assert result.model_log_loss > 0
    assert result.market_log_loss > 0


def test_invalid_evaluation_parameters_are_rejected():
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01"]),
            "Time": ["15:00"],
            "HomeTeam": ["A"],
            "AwayTeam": ["B"],
            "FTHG": [1],
            "FTAG": [0],
            "Avg>2.5": [2.0],
            "Avg<2.5": [2.0],
        }
    )
    with pytest.raises(ValueError):
        evaluate_ou_walk_forward(frame, window=0)
    with pytest.raises(ValueError):
        evaluate_ou_walk_forward(frame, min_ev=-0.01)
