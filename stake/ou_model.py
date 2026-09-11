from __future__ import annotations

import math


def poisson_over_25_probability(expected_total_goals: float) -> float:
    """Return P(total goals > 2.5) for a Poisson total-goals model.

    For a Poisson random variable X with mean lambda:
        P(X > 2) = 1 - exp(-lambda) * (1 + lambda + lambda^2 / 2)

    The function is deliberately small and transparent so the probability
    transformation can be tested independently from the goal estimator.
    """
    if not math.isfinite(expected_total_goals) or expected_total_goals <= 0:
        raise ValueError("expected_total_goals must be a finite positive number")

    probability = 1.0 - math.exp(-expected_total_goals) * (
        1.0 + expected_total_goals + (expected_total_goals**2) / 2.0
    )
    return min(1.0, max(0.0, probability))


def poisson_under_25_probability(expected_total_goals: float) -> float:
    """Return P(total goals < 2.5) under the same Poisson model."""
    return 1.0 - poisson_over_25_probability(expected_total_goals)
