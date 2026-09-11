import math

import pytest

from stake.ou_model import (
    poisson_over_25_probability,
    poisson_under_25_probability,
)


def test_poisson_over_25_known_value():
    # lambda=1 has P(X>2) ~= 0.0803014.
    assert poisson_over_25_probability(1.0) == pytest.approx(0.0803014, rel=1e-6)


def test_over_and_under_sum_to_one():
    over = poisson_over_25_probability(2.5)
    under = poisson_under_25_probability(2.5)
    assert over + under == pytest.approx(1.0)


def test_probability_increases_with_expected_goals():
    low = poisson_over_25_probability(1.5)
    high = poisson_over_25_probability(3.0)
    assert 0 < low < high < 1


def test_invalid_expected_goals_are_rejected():
    for value in (0, -1, math.inf, -math.inf, math.nan):
        with pytest.raises(ValueError):
            poisson_over_25_probability(value)
