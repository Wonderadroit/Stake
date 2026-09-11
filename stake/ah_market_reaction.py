from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd

from stake.baseline import fair_two_way_probability
from stake.goal_model import add_rolling_goal_estimates


@dataclass(frozen=True)
class AHReactionBucket:
    label: str
    observations: int
    mean_abs_gap: float
    model_direction_rate: float
    mean_home_probability_move: float


@dataclass(frozen=True)
class AHReactionEvaluation:
    observations: int
    directional_observations: int
    direction_accuracy: float
    mean_home_probability_move: float
    buckets: tuple[AHReactionBucket, ...]


BUCKETS = (
    ("0-0.25", 0.0, 0.25),
    ("0.25-0.5", 0.25, 0.5),
    ("0.5-1.0", 0.5, 1.0),
    ("1.0+", 1.0, math.inf),
)


def evaluate_ah_market_reaction(frame: pd.DataFrame, *, window: int = 10) -> AHReactionEvaluation:
    """Test whether opening AH disagreement predicts later market repricing.

    Standard Football-Data E0 files provide one handicap line (AHh) plus
    opening and closing AH prices. They do not provide a separate closing
    handicap line, so this experiment measures repricing with normalized
    two-way home probability rather than inventing a closing handicap.
    Closing prices are an outcome of the test and never enter model direction.
    """
    if window < 1:
        raise ValueError("window must be positive")

    required = {"AHh", "AvgAHH", "AvgAHA", "AvgCAHH", "AvgCAHA"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing AH reaction columns: {sorted(missing)}")

    ordered = frame.sort_values(["Date", "Time"], na_position="last").reset_index(drop=True)
    modeled = add_rolling_goal_estimates(ordered, window=window)

    rows: list[dict[str, float]] = []
    for _, row in modeled.iterrows():
        try:
            model_home = float(row["ModelHomeGoals"])
            model_away = float(row["ModelAwayGoals"])
            line = float(row["AHh"])
            open_home = float(row["AvgAHH"])
            open_away = float(row["AvgAHA"])
            close_home = float(row["AvgCAHH"])
            close_away = float(row["AvgCAHA"])
        except (TypeError, ValueError):
            continue

        values = (model_home, model_away, line, open_home, open_away, close_home, close_away)
        if not all(math.isfinite(x) for x in values):
            continue
        if not all(x > 1.0 for x in (open_home, open_away, close_home, close_away)):
            continue

        open_prob, _ = fair_two_way_probability(open_home, open_away)
        close_prob, _ = fair_two_way_probability(close_home, close_away)
        rows.append(
            {
                "gap": model_home - model_away - line,
                "home_probability_move": close_prob - open_prob,
            }
        )

    if not rows:
        raise ValueError("No valid AH opening/closing observations available")

    directional = [r for r in rows if r["gap"] != 0.0 and r["home_probability_move"] != 0.0]
    hits = [
        (r["gap"] > 0 and r["home_probability_move"] > 0)
        or (r["gap"] < 0 and r["home_probability_move"] < 0)
        for r in directional
    ]

    bucket_rows: list[AHReactionBucket] = []
    for label, lower, upper in BUCKETS:
        selected = [r for r in rows if lower <= abs(r["gap"]) < upper]
        selected_directional = [
            r for r in selected if r["gap"] != 0.0 and r["home_probability_move"] != 0.0
        ]
        selected_hits = [
            (r["gap"] > 0 and r["home_probability_move"] > 0)
            or (r["gap"] < 0 and r["home_probability_move"] < 0)
            for r in selected_directional
        ]
        bucket_rows.append(
            AHReactionBucket(
                label=label,
                observations=len(selected),
                mean_abs_gap=(sum(abs(r["gap"]) for r in selected) / len(selected)) if selected else 0.0,
                model_direction_rate=(sum(selected_hits) / len(selected_hits)) if selected_hits else 0.0,
                mean_home_probability_move=(
                    sum(r["home_probability_move"] for r in selected) / len(selected)
                    if selected else 0.0
                ),
            )
        )

    return AHReactionEvaluation(
        observations=len(rows),
        directional_observations=len(directional),
        direction_accuracy=(sum(hits) / len(hits)) if hits else 0.0,
        mean_home_probability_move=sum(r["home_probability_move"] for r in rows) / len(rows),
        buckets=tuple(bucket_rows),
    )
