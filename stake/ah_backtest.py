from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd

from stake.data import asian_handicap_settlement
from stake.goal_model import add_rolling_goal_estimates


@dataclass(frozen=True)
class AHSettlementDistribution:
    full_win: float
    half_win: float
    push: float
    half_loss: float
    full_loss: float

    @property
    def positive_settlement_probability(self) -> float:
        return self.full_win + self.half_win

    @property
    def negative_settlement_probability(self) -> float:
        return self.half_loss + self.full_loss

    @property
    def expected_settlement(self) -> float:
        return (
            self.full_win
            + 0.5 * self.half_win
            - 0.5 * self.half_loss
            - self.full_loss
        )

    @property
    def fair_decimal_odds(self) -> float | None:
        positive = self.full_win + 0.5 * self.half_win
        negative = 0.5 * self.half_loss + self.full_loss
        if positive <= 0:
            return None
        return 1.0 + negative / positive


@dataclass(frozen=True)
class AHBucket:
    label: str
    observations: int
    mean_abs_gap: float
    mean_model_ev: float
    positive_settlement_rate: float
    opening_roi: float


@dataclass(frozen=True)
class AHEvaluation:
    observations: int
    candidate_bets: int
    candidate_roi: float | None
    buckets: tuple[AHBucket, ...]


BUCKETS = (
    ("0-0.25", 0.0, 0.25),
    ("0.25-0.5", 0.25, 0.5),
    ("0.5-1.0", 0.5, 1.0),
    ("1.0+", 1.0, math.inf),
)


def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def _ah_distribution(
    home_goals: float, away_goals: float, line: float, *, max_goals: int = 12
) -> AHSettlementDistribution:
    """Calculate exact model probabilities for every AH settlement outcome."""
    if home_goals <= 0 or away_goals <= 0:
        raise ValueError("Expected goals must be positive")
    if max_goals < 1:
        raise ValueError("max_goals must be positive")

    home_probs = [_poisson_pmf(k, home_goals) for k in range(max_goals + 1)]
    away_probs = [_poisson_pmf(k, away_goals) for k in range(max_goals + 1)]
    buckets = {1.0: 0.0, 0.5: 0.0, 0.0: 0.0, -0.5: 0.0, -1.0: 0.0}
    for hg, hp in enumerate(home_probs):
        for ag, ap in enumerate(away_probs):
            settlement = asian_handicap_settlement(hg, ag, line)
            buckets[settlement] += hp * ap

    return AHSettlementDistribution(
        full_win=buckets[1.0],
        half_win=buckets[0.5],
        push=buckets[0.0],
        half_loss=buckets[-0.5],
        full_loss=buckets[-1.0],
    )


def _expected_ah_settlement(
    home_goals: float, away_goals: float, line: float, *, max_goals: int = 12
) -> float:
    """Expected net settlement for a 1-unit home AH stake under Poisson goals."""
    return _ah_distribution(home_goals, away_goals, line, max_goals=max_goals).expected_settlement


def _expected_profit(expected_settlement: float, odds: float) -> float:
    positive = max(expected_settlement, 0.0)
    negative = min(expected_settlement, 0.0)
    return positive * (odds - 1.0) + negative


def _realized_profit(settlement: float, odds: float) -> float:
    if settlement >= 0:
        return settlement * (odds - 1.0)
    return settlement


def evaluate_ah_walk_forward(
    frame: pd.DataFrame,
    *,
    window: int = 10,
    min_ev: float = 0.03,
) -> AHEvaluation:
    """Evaluate exact Poisson AH settlement probabilities walk-forward."""
    if window < 1:
        raise ValueError("window must be positive")
    if min_ev < 0:
        raise ValueError("min_ev must be non-negative")

    ordered = frame.sort_values(["Date", "Time"], na_position="last").reset_index(drop=True)
    modeled = add_rolling_goal_estimates(ordered, window=window)

    rows: list[dict[str, float]] = []
    for _, row in modeled.iterrows():
        if pd.isna(row["ModelHomeGoals"]) or pd.isna(row["ModelAwayGoals"]):
            continue
        try:
            line = float(row["AHh"])
            home_odds = float(row["AvgAHH"])
            away_odds = float(row["AvgAHA"])
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(x) and x > 1.0 for x in (home_odds, away_odds)):
            continue
        if not math.isfinite(line):
            continue

        distribution = _ah_distribution(
            float(row["ModelHomeGoals"]), float(row["ModelAwayGoals"]), line
        )
        home_ev = _expected_profit(distribution.expected_settlement, home_odds)
        away_ev = _expected_profit(-distribution.expected_settlement, away_odds)
        actual_home = asian_handicap_settlement(int(row["FTHG"]), int(row["FTAG"]), line)
        gap = float(row["ModelHomeGoals"]) - float(row["ModelAwayGoals"]) - line
        rows.append(
            {
                "gap": gap,
                "home_ev": home_ev,
                "away_ev": away_ev,
                "actual_home": actual_home,
                "home_odds": home_odds,
                "away_odds": away_odds,
                "expected_settlement": distribution.expected_settlement,
            }
        )

    if not rows:
        raise ValueError("No valid AH observations available for evaluation")

    candidate_profits: list[float] = []
    for item in rows:
        if item["home_ev"] >= min_ev:
            candidate_profits.append(_realized_profit(item["actual_home"], item["home_odds"]))
        elif item["away_ev"] >= min_ev:
            candidate_profits.append(_realized_profit(-item["actual_home"], item["away_odds"]))

    bucket_rows: list[AHBucket] = []
    for label, lower, upper in BUCKETS:
        selected = [r for r in rows if lower <= abs(r["gap"]) < upper]
        if not selected:
            bucket_rows.append(AHBucket(label, 0, 0.0, 0.0, 0.0, 0.0))
            continue

        profits: list[float] = []
        positive = 0
        evs: list[float] = []
        for item in selected:
            if item["gap"] >= 0:
                settlement = item["actual_home"]
                odds = item["home_odds"]
                evs.append(item["home_ev"])
            else:
                settlement = -item["actual_home"]
                odds = item["away_odds"]
                evs.append(item["away_ev"])
            positive += settlement > 0
            profits.append(_realized_profit(settlement, odds))

        bucket_rows.append(
            AHBucket(
                label=label,
                observations=len(selected),
                mean_abs_gap=sum(abs(r["gap"]) for r in selected) / len(selected),
                mean_model_ev=sum(evs) / len(evs),
                positive_settlement_rate=positive / len(selected),
                opening_roi=sum(profits) / len(profits),
            )
        )

    return AHEvaluation(
        observations=len(rows),
        candidate_bets=len(candidate_profits),
        candidate_roi=(sum(candidate_profits) / len(candidate_profits)) if candidate_profits else None,
        buckets=tuple(bucket_rows),
    )
