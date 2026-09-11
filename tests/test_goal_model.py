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

    # A has one prior home match: 2 scored, 0 conceded.
    # B has no prior away match, so the model uses its 1.35 prior.
    assert estimate.home_goals == 1.675
    assert estimate.away_goals == 0.675


def test_rolling_estimates_do_not_use_current_result():
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(
                ["2024-01-01", "2024-01-08", "2024-01-15", "2024-01-22"]
            ),
            "Time": ["15:00", "15:00", "15:00", "15:00"],
            "HomeTeam": ["A", "B", "A", "A"],
            "AwayTeam": ["B", "A", "B", "B"],
            "FTHG": [2, 0, 3, 999],
            "FTAG": [0, 1, 1, 999],
        }
    )
    result = add_rolling_goal_estimates(frame)

    # First fixture has no prior history.
    assert pd.isna(result.loc[0, "ModelTotalGoals"])

    # Second fixture has no prior home history for B, so it cannot
    # produce a complete estimate under the current venue-specific model.
    assert pd.isna(result.loc[1, "ModelTotalGoals"])

    # The current fixture's 3-1 result must not affect its own estimate.
    assert result.loc[2, "ModelTotalGoals"] < 10

    # The deliberately absurd 999-999 result must not affect the
    # estimate for the fourth fixture because it is the current result.
    assert result.loc[3, "ModelTotalGoals"] < 10
