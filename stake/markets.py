from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketSnapshot:
    """A market observation frozen at a specific pre-match timestamp."""

    odds: float
    line: float | None = None

    def implied_probability(self) -> float:
        if self.odds <= 1.0:
            raise ValueError("Decimal odds must be greater than 1.0")
        return 1.0 / self.odds


def remove_overround(probabilities: list[float]) -> list[float]:
    """Normalize mutually-exclusive implied probabilities."""
    if not probabilities or any(p <= 0 for p in probabilities):
        raise ValueError("Probabilities must be positive")
    total = sum(probabilities)
    if total <= 0:
        raise ValueError("Probability sum must be positive")
    return [p / total for p in probabilities]
