import pandas as pd
import pytest

from stake.baseline import brier_score, fair_two_way_probability
from stake.backtest import BetResult, hit_rate, roi
from stake.data import chronological_split
from stake.diagnostic import Hypothesis, diagnose
from stake.markets import MarketSnapshot, remove_overround


def test_market_implied_probability():
    assert MarketSnapshot(2.0).implied_probability() == pytest.approx(0.5)


def test_two_way_market_removes_overround():
    a, b = fair_two_way_probability(1.8, 2.2)
    assert a + b == pytest.approx(1.0)


def test_chronological_split_never_shuffles():
    frame = pd.DataFrame({"Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]), "x": [1, 2, 3]})
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
