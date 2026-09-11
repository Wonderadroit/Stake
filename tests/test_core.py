from pathlib import Path

import pandas as pd
import pytest

from stake.baseline import brier_score, fair_two_way_probability
from stake.backtest import BetResult, hit_rate, roi
from stake.data import (
    asian_handicap_settlement,
    chronological_split,
    load_match_csv,
    load_seasons,
    over_under_25_settlement,
    validate_market_columns,
)
from stake.diagnostic import Hypothesis, diagnose
from stake.markets import MarketSnapshot, remove_overround


def test_market_implied_probability():
    assert MarketSnapshot(2.0).implied_probability() == pytest.approx(0.5)


def test_two_way_market_removes_overround():
    a, b = fair_two_way_probability(1.8, 2.2)
    assert a + b == pytest.approx(1.0)


def test_chronological_split_never_shuffles():
    frame = pd.DataFrame(
        {"Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]), "x": [1, 2, 3]}
    )
    train, test = chronological_split(frame, test_fraction=1 / 3)
    assert train["x"].tolist() == [1, 2]
    assert test["x"].tolist() == [3]


def test_fragile_diagnosis_is_pass():
    result = diagnose(Hypothesis("H1", [3]), Hypothesis("H2", [0]), causal_depth=4)
    assert result.selected is None


def test_insufficient_separation_is_pass():
    result = diagnose(Hypothesis("H1", [2]), Hypothesis("H2", [1]), causal_depth=2)
    assert result.selected is None


def test_diagnostic_selects_clear_hypothesis():
    result = diagnose(Hypothesis("H1", [4]), Hypothesis("H2", [1]), causal_depth=2)
    assert result.selected == "H1"
    assert result.separation == 3


def test_backtest_metrics():
    results = [BetResult(2.0, True), BetResult(2.0, False)]
    assert hit_rate(results) == pytest.approx(0.5)
    assert roi(results) == pytest.approx(0.0)


def test_brier_score():
    assert brier_score([0.5, 0.5], [1, 0]) == pytest.approx(0.25)


def test_overround_normalization():
    values = remove_overround([0.6, 0.6])
    assert values == pytest.approx([0.5, 0.5])


def test_market_columns_are_validated():
    frame = pd.DataFrame({"AHh": [0.5], "AvgAHH": [1.9], "AvgAHA": [2.0], "Avg>2.5": [2.1], "Avg<2.5": [1.8]})
    validate_market_columns(frame)


def test_missing_market_column_is_rejected():
    frame = pd.DataFrame({"AHh": [0.5], "AvgAHH": [1.9]})
    with pytest.raises(ValueError, match="Missing market columns"):
        validate_market_columns(frame)


def test_asian_handicap_full_win_and_loss():
    assert asian_handicap_settlement(2, 0, 0.5) == 1.0
    assert asian_handicap_settlement(0, 2, 0.5) == -1.0


def test_asian_handicap_push():
    assert asian_handicap_settlement(1, 1, 0.0) == 0.0


def test_asian_handicap_quarter_line_half_win():
    # Home +0.25 in a draw = half win + push -> +0.5 overall.
    assert asian_handicap_settlement(1, 1, 0.25) == 0.5


def test_over_under_25_settlement():
    assert over_under_25_settlement(2, 1, over=True) == 1.0
    assert over_under_25_settlement(1, 1, over=True) == -1.0
    assert over_under_25_settlement(1, 1, over=False) == 1.0


def test_load_real_historical_file_if_present():
    path = Path("data/raw/E0_2223.csv")
    if not path.exists():
        pytest.skip("historical dataset not present in this checkout")
    frame = load_match_csv(path)
    assert len(frame) == 380
    validate_market_columns(frame)
    assert frame["Date"].is_monotonic_increasing


def test_load_multiple_seasons_if_present():
    paths = [Path(f"data/raw/E0_{season}.csv") for season in ("2122", "2223", "2324")]
    if not all(path.exists() for path in paths):
        pytest.skip("historical datasets not present in this checkout")
    frame = load_seasons(paths)
    assert len(frame) == 1140
    assert frame["SeasonSource"].nunique() == 3
    assert frame["Date"].is_monotonic_increasing
