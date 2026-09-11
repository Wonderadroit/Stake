import pandas as pd

from stake.goal_model import add_rolling_goal_estimates, estimate_goals


def test_goal_estimate_uses_only_prior_matches():
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
            "Time": ["15:00", "15:00", "15:00"],
            "HomeTeam": ["A", "B", "A"],
            "AwayTeam": ["B", "A", "B"],
            "FTHG": [2, 0, 99],
            "FTAG": [0, 1, 99],
        }
    )
    estimate = estimate_goals(frame.iloc[:2], "A", "B", window=10)
    assert estimate is not None
    assert estimate.home_goals == 1.5
    assert estimate.away_goals == 0.5


def test_rolling_estimates_do_not_use_current_result():
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
            "Time": ["15:00", "15:00", "15:00"],
            "HomeTeam": ["A", "B", "A"],
            "AwayTeam": ["B", "A", "B"],
            "FTHG": [2, 0, 100],
            "FTAG": [0, 1, 100],
        }
    )
    result = add_rolling_goal_estimates(frame)
    assert pd.isna(result.loc[0, "ModelTotalGoals"])
    assert result.loc[1, "ModelTotalGoals"] > 0
    assert result.loc[2, "ModelTotalGoals"] < 10
