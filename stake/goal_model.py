from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class GoalEstimate:
    """Pre-match expected-goal estimate for a single fixture."""

    home_goals: float
    away_goals: float

    @property
    def total_goals(self) -> float:
        return self.home_goals + self.away_goals


def _team_history(
    history: pd.DataFrame, team: str, venue: str, window: int
) -> tuple[float, float, int]:
    """Return recent venue-specific history, falling back to all venues.

    The fallback uses only matches already present in ``history``. It improves
    early-season coverage when a team has played before but has not yet played
    at the required venue. A team with no prior matches remains unavailable.
    """
    if venue == "home":
        rows = history[history["HomeTeam"] == team].tail(window)
        if rows.empty:
            rows = history[
                (history["HomeTeam"] == team) | (history["AwayTeam"] == team)
            ].tail(window)
            if rows.empty:
                return 0.0, 0.0, 0
            scored = rows.apply(
                lambda r: r["FTHG"] if r["HomeTeam"] == team else r["FTAG"], axis=1
            )
            conceded = rows.apply(
                lambda r: r["FTAG"] if r["HomeTeam"] == team else r["FTHG"], axis=1
            )
            return float(scored.mean()), float(conceded.mean()), len(rows)
        scored, conceded = rows["FTHG"], rows["FTAG"]
    elif venue == "away":
        rows = history[history["AwayTeam"] == team].tail(window)
        if rows.empty:
            rows = history[
                (history["HomeTeam"] == team) | (history["AwayTeam"] == team)
            ].tail(window)
            if rows.empty:
                return 0.0, 0.0, 0
            scored = rows.apply(
                lambda r: r["FTHG"] if r["HomeTeam"] == team else r["FTAG"], axis=1
            )
            conceded = rows.apply(
                lambda r: r["FTAG"] if r["HomeTeam"] == team else r["FTHG"], axis=1
            )
            return float(scored.mean()), float(conceded.mean()), len(rows)
        scored, conceded = rows["FTAG"], rows["FTHG"]
    else:
        raise ValueError("venue must be 'home' or 'away'")
    return float(scored.mean()), float(conceded.mean()), len(rows)


def estimate_goals(
    history: pd.DataFrame,
    home_team: str,
    away_team: str,
    *,
    window: int = 10,
    prior_goals: float = 1.35,
) -> GoalEstimate | None:
    """Estimate goals using only matches strictly before the target fixture.

    Venue-specific history is preferred. If a team has prior matches but none
    at the required venue, its recent all-venue history is used. If neither
    team has any prior history, the fixture is not modeled.
    """
    if window < 1:
        raise ValueError("window must be positive")
    if prior_goals <= 0:
        raise ValueError("prior_goals must be positive")

    hs, hc, hn = _team_history(history, home_team, "home", window)
    as_, ac, an = _team_history(history, away_team, "away", window)
    if hn == 0 and an == 0:
        return None

    hs = hs if hn else prior_goals
    hc = hc if hn else prior_goals
    as_ = as_ if an else prior_goals
    ac = ac if an else prior_goals
    return GoalEstimate(max(0.05, (hs + ac) / 2), max(0.05, (as_ + hc) / 2))


def add_rolling_goal_estimates(frame: pd.DataFrame, *, window: int = 10) -> pd.DataFrame:
    """Add walk-forward expected goals without using future observations."""
    ordered = frame.sort_values(["Date", "Time"], na_position="last").reset_index(drop=True)
    estimates = []
    for idx, row in ordered.iterrows():
        estimates.append(
            estimate_goals(
                ordered.iloc[:idx],
                str(row["HomeTeam"]),
                str(row["AwayTeam"]),
                window=window,
            )
        )

    result = ordered.copy()
    result["ModelHomeGoals"] = [e.home_goals if e else None for e in estimates]
    result["ModelAwayGoals"] = [e.away_goals if e else None for e in estimates]
    result["ModelTotalGoals"] = [e.total_goals if e else None for e in estimates]
    return result
