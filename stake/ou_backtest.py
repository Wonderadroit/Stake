from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd

from stake.baseline import brier_score, fair_two_way_probability, log_loss
from stake.goal_model import add_rolling_goal_estimates
from stake.ou_model import poisson_over_25_probability


@dataclass(frozen=True)
class OUEvaluation:
    observations: int
    model_brier: float
    market_brier: float
    model_log_loss: float
    market_log_loss: float
    candidate_bets: int
    candidate_roi: float | None


def _valid_odds(value: object) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 1.0
    except (TypeError, ValueError):
        return False


def evaluate_ou_walk_forward(
    frame: pd.DataFrame,
    *,
    window: int = 10,
    min_ev: float = 0.03,
) -> OUEvaluation:
    """Evaluate the simple goal model strictly walk-forward.

    The model only sees matches before each fixture. Opening O/U prices are
    used as the market comparator. A candidate bet is recorded only when the
    model's probability produces at least ``min_ev`` expected return at the
    actual opening price. No closing information enters the decision.
    """
    if window < 1:
        raise ValueError("window must be positive")
    if min_ev < 0:
        raise ValueError("min_ev must be non-negative")

    ordered = frame.sort_values(["Date", "Time"], na_position="last").reset_index(drop=True)
    modeled = add_rolling_goal_estimates(ordered, window=window)

    model_probs: list[float] = []
    market_probs: list[float] = []
    outcomes: list[int] = []
    candidate_profits: list[float] = []

    for _, row in modeled.iterrows():
        model_total = row["ModelTotalGoals"]
        if pd.isna(model_total):
            continue

        if not (_valid_odds(row.get("Avg>2.5")) and _valid_odds(row.get("Avg<2.5"))):
            continue

        market_over, market_under = fair_two_way_probability(
            float(row["Avg>2.5"]), float(row["Avg<2.5"])
        )
        model_over = poisson_over_25_probability(float(model_total))
        outcome = int(int(row["FTHG"]) + int(row["FTAG"]) > 2)

        model_probs.append(model_over)
        market_probs.append(market_over)
        outcomes.append(outcome)

        over_ev = model_over * float(row["Avg>2.5"]) - 1.0
        under_ev = (1.0 - model_over) * float(row["Avg<2.5"]) - 1.0
        if over_ev >= min_ev:
            candidate_profits.append(
                float(row["Avg>2.5"]) - 1.0 if outcome else -1.0
            )
        elif under_ev >= min_ev:
            candidate_profits.append(
                float(row["Avg<2.5"]) - 1.0 if not outcome else -1.0
            )

    if not outcomes:
        raise ValueError("No valid O/U observations available for evaluation")

    return OUEvaluation(
        observations=len(outcomes),
        model_brier=brier_score(model_probs, outcomes),
        market_brier=brier_score(market_probs, outcomes),
        model_log_loss=log_loss(model_probs, outcomes),
        market_log_loss=log_loss(market_probs, outcomes),
        candidate_bets=len(candidate_profits),
        candidate_roi=(sum(candidate_profits) / len(candidate_profits)) if candidate_profits else None,
    )
