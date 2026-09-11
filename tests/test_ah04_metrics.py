import pytest

from stake.ah04_metrics import (
    asian_implied_probabilities,
    classify_probability_pressure,
    probability_displacement,
)


def test_asian_prices_are_normalized_to_two_way_probability():
    home, away = asian_implied_probabilities(1.0, 1.0)
    assert home == pytest.approx(0.5)
    assert away == pytest.approx(0.5)
    assert home + away == pytest.approx(1.0)


def test_probability_displacement_identifies_home_pressure():
    obs = probability_displacement(1.0, 1.0, 0.8, 1.2)
    assert obs.home_delta > 0
    assert obs.away_delta < 0
    assert obs.direction == "HOME"


def test_probability_displacement_identifies_away_pressure():
    obs = probability_displacement(1.0, 1.0, 1.2, 0.8)
    assert obs.home_delta < 0
    assert obs.away_delta > 0
    assert obs.direction == "AWAY"


def test_pressure_threshold_is_probability_space_not_raw_odds_space():
    assert classify_probability_pressure(0.02, -0.02, threshold=0.015) == "HOME_PRESSURE"
    assert classify_probability_pressure(0.01, -0.01, threshold=0.015) == "UNCHANGED"
    assert classify_probability_pressure(-0.02, 0.02, threshold=0.015) == "AWAY_PRESSURE"
