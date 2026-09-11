import pandas as pd
import pytest

from stake.ah_market_reaction import evaluate_ah_market_reaction


def _frame(close_home: float = 1.70, close_away: float = 2.20) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15"]),
            "Time": ["15:00"] * 3,
            "HomeTeam": ["A", "B", "A"],
            "AwayTeam": ["B", "A", "B"],
            "FTHG": [2, 0, 99],
            "FTAG": [0, 1, 99],
            "AHh": [0.0, 0.0, 0.0],
            "AvgAHH": [2.00, 2.00, 2.00],
            "AvgAHA": [1.80, 1.80, 1.80],
            "AvgCAHH": [close_home, close_home, close_home],
            "AvgCAHA": [close_away, close_away, close_away],
        }
    )


def test_reaction_uses_closing_prices_only_as_outcome():
    result = evaluate_ah_market_reaction(_frame())
    assert result.observations == 2
    assert result.directional_observations == 2
    assert result.mean_home_probability_move != 0


def test_reaction_rejects_missing_closing_prices():
    frame = _frame().drop(columns=["AvgCAHH"])
    with pytest.raises(ValueError, match="Missing AH reaction columns"):
        evaluate_ah_market_reaction(frame)


def test_current_fixture_result_cannot_change_model_direction():
    first = evaluate_ah_market_reaction(_frame())
    changed = _frame().copy()
    changed.loc[2, "FTHG"] = 10000
    changed.loc[2, "FTAG"] = 0
    second = evaluate_ah_market_reaction(changed)
    assert first.direction_accuracy == second.direction_accuracy
    assert first.mean_home_probability_move == second.mean_home_probability_move
