from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd

from stake.baseline import fair_two_way_probability
from stake.goal_model import add_rolling_goal_estimates
from stake.ou_model import poisson_over_25_probability


@dataclass(frozen=True)
class DisagreementBucket:
    label: str
    observations: int
    mean_gap: float
    realized_roi: float
    win_rate: float


@dataclass(frozen=True)
class OUDisagreementEvaluation:
    observations: int
    buckets: tuple[DisagreementBucket, ...]


BUCKETS = (
    (0.00, 0.02, "0-2%"),
    (0.02, 0.05, "2-5%"),
    (0.05, 0.10, "5-10%"),
    (0.10, float("inf"), "10%+"),
)


def _valid_odds(value: object) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 1.0
    except (TypeError, ValueError):
        return False


def _bucket_for_gap(gap: float) -> str | None:
    magnitude = abs(gap)
    for lower, upper, label in BUCKETS:
        if lower <= magnitude < upper:
            return label
    return None


def evaluate_ou_disagreement(
    frame: pd.DataFrame,
    *,
    window: int = 10,
) -> OUDisagreementEvaluation:
    """Probe whether model/market disagreement contains information.

    The goal is deliberately narrower than a betting strategy. For every
    valid fixture, the simple walk-forward goal model is compared with the
    opening O/U 2.5 market probability. The side selected by the direction of
    the disagreement is then scored at the actual opening price.

    No threshold is optimized on the results. Outcomes are reported in fixed
    disagreement buckets so the experiment can test whether larger model
    disagreement is associated with better or worse realized performance.
    """
    if window < 1:
        raise ValueError("window must be positive")

    ordered = frame.sort_values(["Date", "Time"], na_position="last").reset_index(drop=True)
    modeled = add_rolling_goal_estimates(ordered, window=window)
    rows: dict[str, list[float]] = {label: [] for _, _, label in BUCKETS}
    wins: dict[str, list[int]] = {label: [] for _, _, label in BUCKETS}
    gaps: dict[str, list[float]] = {label: [] for _, _, label in BUCKETS}

    for _, row in modeled.iterrows():
        model_total = row["ModelTotalGoals"]
        if pd.isna(model_total):
            continue
        if not (_valid_odds(row.get("Avg>2.5")) and _valid_odds(row.get("Avg<2.5"))):
            continue

        market_over, _ = fair_two_way_probability(
            float(row["Avg>2.5"]), float(row["Avg<2.5"])
        )
        model_over = poisson_over_25_probability(float(model_total))
        gap = model_over - market_over
        label = _bucket_for_gap(gap)
        if label is None or abs(gap) < 1e-12:
            continue

        outcome_over = int(int(row["FTHG"]) + int(row["FTAG"]) > 2)
        if gap > 0:
            odds = float(row["Avg>2.5"])
            won = outcome_over == 1
        else:
            odds = float(row["Avg<2.5"])
            won = outcome_over == 0

        profit = odds - 1.0 if won else -1.0
        rows[label].append(profit)
        wins[label].append(int(won))
        gaps[label].append(abs(gap))

    buckets: list[DisagreementBucket] = []
    for _, _, label in BUCKETS:
        profits = rows[label]
        if not profits:
            continue
        buckets.append(
            DisagreementBucket(
                label=label,
                observations=len(profits),
                mean_gap=sum(gaps[label]) / len(gaps[label]),
                realized_roi=sum(profits) / len(profits),
                win_rate=sum(wins[label]) / len(wins[label]),
            )
        )

    return OUDisagreementEvaluation(
        observations=sum(bucket.observations for bucket in buckets),
        buckets=tuple(buckets),
    )
