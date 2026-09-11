from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd

from stake.data import asian_handicap_settlement
from stake.goal_model import add_rolling_goal_estimates


@dataclass(frozen=True)
class AHBucket:
    label: str
    observations: int
    mean_abs_gap: float
    win_rate: float
    opening_roi: float


@dataclass(frozen=True)
class AHEvaluation:
    observations: int
    model_brier: float
    market_brier: float
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


def _expected_ah_settlement(
    home_goals: float, away_goals: float, line: float, *, max_goals: int = 12
) -> float:
    """Expected net settlement for a 1-unit home AH stake under Poisson goals."""
    if home_goals <= 0 or away_goals <= 0:
        raise ValueError("Expected goals must be positive")
    if max_goals < 1:
        raise ValueError("max_goals must be positive")

    home_probs = [_poisson_pmf(k, home_goals) for k in range(max_goals + 1)]
    away_probs = [_poisson_pmf(k, away_goals) for k in range(max_goals + 1)]
    total = 0.0
    mass = 0.0
    for hg, hp in enumerate(home_probs):
        for ag, ap in enumerate(away_probs):
            p = hp * ap
            mass += p
            total += p * asian_handicap_settlement(hg, ag, line)
    # The omitted tail is tiny at ordinary football scoring rates. Do not
    # silently renormalize it; retaining the lost mass is conservative.
    return total


def _expected_profit(expected_settlement: float, odds: float) -> float:
    """Convert expected AH settlement into expected decimal-odds profit."""
    positive = max(expected_settlement, 0.0)
    negative = min(expected_settlement, 0.0)
    return positive * (odds - 1.0) + negative


def evaluate_ah_walk_forward(
    frame: pd.DataFrame,
    *,
    window: int = 10,
    min_ev: float = 0.03,
) -> AHEvaluation:
    """Probe whether a walk-forward goal model disagrees usefully with AH.

    The model sees only matches before each fixture. It converts expected goals
    into a Poisson goal-difference distribution, then estimates AH settlement
    against the opening handicap. No closing price or post-match statistic is
    used for the decision.
    """
    if window < 1:
        raise ValueError("window must be positive")
    if min_ev < 0:
        raise ValueError("min_ev must be non-negative")

    ordered = frame.sort_values(["Date", "Time"], na_position="last").reset_index(drop=True)
    modeled = add_rolling_goal_estimates(ordered, window=window)

    rows: list[dict[str, float | int | str]] = []
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

        expected_home = _expected_ah_settlement(
            float(row["ModelHomeGoals"]), float(row["ModelAwayGoals"]), line
        )
        expected_away = -expected_home
        home_ev = _expected_profit(expected_home, home_odds)
        away_ev = _expected_profit(expected_away, away_odds)
        actual_home = asian_handicap_settlement(
            int(row["FTHG"]), int(row["FTAG"]), line
        )

        gap = float(row["ModelHomeGoals"]) - float(row["ModelAwayGoals"]) - line
        rows.append(
            {
                "gap": gap,
                "home_ev": home_ev,
                "away_ev": away_ev,
                "actual_home": actual_home,
                "home_odds": home_odds,
                "away_odds": away_odds,
            }
        )

    if not rows:
        raise ValueError("No valid AH observations available for evaluation")

    # A market-free diagnostic target: probability that the home side settles
    # positively. Pushes and half outcomes are not treated as full wins.
    model_scores: list[float] = []
    outcomes: list[float] = []
    candidate_profits: list[float] = []
    for item in rows:
        # Convert expected settlement to a bounded directional score. This is
        # deliberately only a diagnostic score, not a claimed fair probability.
        score = 0.5 + 0.5 * math.tanh(item["gap"])
        model_scores.append(score)
        actual = item["actual_home"]
        outcomes.append(1.0 if actual > 0 else 0.0)
        if item["home_ev"] >= min_ev:
            s = actual
            candidate_profits.append(
                s * (item["home_odds"] - 1.0) if s >= 0 else s
            )
        elif item["away_ev"] >= min_ev:
            s = -actual
            candidate_profits.append(
                s * (item["away_odds"] - 1.0) if s >= 0 else s
            )

    mean_brier = sum((p - y) ** 2 for p, y in zip(model_scores, outcomes)) / len(rows)
    # The market probability comparator is intentionally simple: normalize the
    # two opening prices, while the AH settlement itself remains non-binary.
    market_scores: list[float] = []
    for item in rows:
        hp = 1.0 / item["home_odds"]
        ap = 1.0 / item["away_odds"]
        market_scores.append(hp / (hp + ap))
    market_brier = sum((p - y) ** 2 for p, y in zip(market_scores, outcomes)) / len(rows)

    bucket_rows: list[AHBucket] = []
    for label, lower, upper in BUCKETS:
        selected = [r for r in rows if lower <= abs(r["gap"]) < upper]
        if not selected:
            bucket_rows.append(AHBucket(label, 0, 0.0, 0.0, 0.0))
            continue
        wins = sum(r["actual_home"] > 0 if r["gap"] >= 0 else r["actual_home"] < 0 for r in selected)
        profits: list[float] = []
        for r in selected:
            settlement = r["actual_home"] if r["gap"] >= 0 else -r["actual_home"]
            odds = r["home_odds"] if r["gap"] >= 0 else r["away_odds"]
            profits.append(settlement * (odds - 1.0) if settlement >= 0 else settlement)
        bucket_rows.append(
            AHBucket(
                label,
                len(selected),
                sum(abs(r["gap"]) for r in selected) / len(selected),
                wins / len(selected),
                sum(profits) / len(profits),
            )
        )

    return AHEvaluation(
        observations=len(rows),
        model_brier=mean_brier,
        market_brier=market_brier,
        candidate_bets=len(candidate_profits),
        candidate_roi=(sum(candidate_profits) / len(candidate_profits)) if candidate_profits else None,
        buckets=tuple(bucket_rows),
    )
