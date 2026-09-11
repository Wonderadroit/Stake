from __future__ import annotations

import math


def decimal_to_implied(odds: float) -> float:
    if odds <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.0")
    return 1.0 / odds


def fair_two_way_probability(odds_a: float, odds_b: float) -> tuple[float, float]:
    """Remove bookmaker overround from a two-way market."""
    pa = decimal_to_implied(odds_a)
    pb = decimal_to_implied(odds_b)
    total = pa + pb
    return pa / total, pb / total


def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    if len(probabilities) != len(outcomes) or not probabilities:
        raise ValueError("Probability and outcome arrays must have equal non-zero length")
    if any(not 0 <= p <= 1 for p in probabilities):
        raise ValueError("Probabilities must be in [0, 1]")
    if any(o not in (0, 1) for o in outcomes):
        raise ValueError("Outcomes must be 0 or 1")
    return sum((p - y) ** 2 for p, y in zip(probabilities, outcomes)) / len(outcomes)


def log_loss(probabilities: list[float], outcomes: list[int], eps: float = 1e-12) -> float:
    if len(probabilities) != len(outcomes) or not probabilities:
        raise ValueError("Probability and outcome arrays must have equal non-zero length")
    total = 0.0
    for p, y in zip(probabilities, outcomes):
        p = min(max(p, eps), 1 - eps)
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / len(outcomes)
