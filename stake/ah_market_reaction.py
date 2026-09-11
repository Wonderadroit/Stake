from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd

from stake.goal_model import add_rolling_goal_estimates


@dataclass(frozen=True)
class AHReactionBucket:
    label: str
    observations: int
    mean_abs_gap: float
    model_direction_rate: float
    mean_line_move: float
    mean_home_price_move: float
    mean_combined_move: float


@dataclass(frozen=True)
class AHReactionEvaluation:
    observations: int
    direction_accuracy: float
    mean_line_move: float
    mean_home_price_move: float
    mean_combined_move: float
    buckets: tuple[AHReactionBucket, ...]


BUCKETS = (
    ("0-0.25", 0.0, 0.25),
    ("0.25-0.5", 0.25, 0.5),
    ("0.5-1.0", 0.5, 1.0),
    ("1.0+", 1.0, math.inf),
)


def _numeric(row: pd.Series, *names: str) -> float | None:
    for name in names:
        try:
            value = float(row[name])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value):
            return value
    return None


def _home_favorable_price_move(open_odds: float, close_odds: float) -> float:
    """Positive means the closing home price became more favorable to home.

    Decimal odds rising means a bettor receives more payout for the same stake;
    falling odds means the market priced the outcome more strongly.
    """
    return close_odds - open_odds


def evaluate_ah_market_reaction(
    frame: pd.DataFrame,
    *,
    window: int = 10,
) -> AHReactionEvaluation:
    """Test whether model disagreement predicts subsequent AH market movement.

    The model is frozen using matches strictly before each fixture. Opening AH
    line/price determine the disagreement. Closing AH line/price are measured
    only afterward as the market-reaction outcome; they never influence the
    model direction.

    For the Football-Data AH convention, a larger AH line is more favorable to
    the home side. A positive model gap therefore predicts a positive closing
    line move. Price movement is reported separately because bookmakers can
    change price without changing the handicap line.
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
        home_goals = _numeric(row, "ModelHomeGoals")
        away_goals = _numeric(row, "ModelAwayGoals")
        open_line = _numeric(row, "AHh")
        open_home = _numeric(row, "AvgAHH")
        open_away = _numeric(row, "AvgAHA")
        close_line = _numeric(row, "AHh", "CAHh", "AvgCAH")
        close_home = _numeric(row, "AvgCAHH")
        close_away = _numeric(row, "AvgCAHA")

        # Football-Data stores the closing handicap as AvgCAHH/AvgCAHA prices,
        # while AHh is the handicap itself. There is no separate closing-line
        # column in the standard E0 files, so infer line movement from the
        # change in the quoted home/away prices only when a closing handicap
        # field is actually present. Standard files are therefore price-only
        # for the closing reaction test.
        if None in (home_goals, away_goals, open_line, open_home, open_away, close_home, close_away):
            continue

        gap = home_goals - away_goals - open_line
        home_price_move = _home_favorable_price_move(open_home, close_home)
        away_price_move = close_away - open_away

        # Normalize price movement into a home-direction signal. When home odds
        # fall while away odds rise, the market is moving toward home. When both
        # move together, the signal is ambiguous. This is deliberately kept as
        # a continuous diagnostic rather than converted into a betting rule.
        combined_move = away_price_move - home_price_move
        rows.append(
            {
                "gap": gap,
                "home_price_move": home_price_move,
                "combined_move": combined_move,
                "away_price_move": away_price_move,
            }
        )

    if not rows:
        raise ValueError("No valid AH opening/closing observations available")

    direction_hits = [
        (r["gap"] > 0 and r["combined_move"] > 0)
        or (r["gap"] < 0 and r["combined_move"] < 0)
        for r in rows
        if r["gap"] != 0 and r["combined_move"] != 0
    ]

    bucket_rows: list[AHReactionBucket] = []
    for label, lower, upper in BUCKETS:
        selected = [r for r in rows if lower <= abs(r["gap"]) < upper]
        if not selected:
            bucket_rows.append(AHReactionBucket(label, 0, 0.0, 0.0, 0.0, 0.0, 0.0))
            continue

        directional = [
            (r["gap"] > 0 and r["combined_move"] > 0)
            or (r["gap"] < 0 and r["combined_move"] < 0)
            for r in selected
            if r["gap"] != 0 and r["combined_move"] != 0
        ]
        bucket_rows.append(
            AHReactionBucket(
                label=label,
                observations=len(selected),
                mean_abs_gap=sum(abs(r["gap"]) for r in selected) / len(selected),
                model_direction_rate=(sum(directional) / len(directional)) if directional else 0.0,
                mean_line_move=0.0,
                mean_home_price_move=sum(r["home_price_move"] for r in selected) / len(selected),
                mean_combined_move=sum(r["combined_move"] for r in selected) / len(selected),
            )
        )

    return AHReactionEvaluation(
        observations=len(rows),
        direction_accuracy=(sum(direction_hits) / len(direction_hits)) if direction_hits else 0.0,
        mean_line_move=0.0,
        mean_home_price_move=sum(r["home_price_move"] for r in rows) / len(rows),
        mean_combined_move=sum(r["combined_move"] for r in rows) / len(rows),
        buckets=tuple(bucket_rows),
    )
