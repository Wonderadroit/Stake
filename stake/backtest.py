from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BetResult:
    odds: float
    won: bool

    @property
    def profit(self) -> float:
        return self.odds - 1.0 if self.won else -1.0


def roi(results: list[BetResult]) -> float:
    if not results:
        raise ValueError("At least one result is required")
    return sum(r.profit for r in results) / len(results)


def hit_rate(results: list[BetResult]) -> float:
    if not results:
        raise ValueError("At least one result is required")
    return sum(r.won for r in results) / len(results)
