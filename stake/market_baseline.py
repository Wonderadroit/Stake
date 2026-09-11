from __future__ import annotations

import math

import pandas as pd

from stake.baseline import fair_two_way_probability
from stake.data import asian_handicap_settlement, over_under_25_settlement, validate_market_columns


def _valid_odds(value: object) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 1.0
    except (TypeError, ValueError):
        return False


def _fair_probs(row: dict[str, object], first: str, second: str) -> tuple[float | None, float | None]:
    if not (_valid_odds(row.get(first)) and _valid_odds(row.get(second))):
        return None, None
    return fair_two_way_probability(float(row[first]), float(row[second]))


def prepare_market_baseline(frame: pd.DataFrame) -> pd.DataFrame:
    """Create pre-match market probabilities and realized settlements.

    Only opening/closing prices, match identity, and final result are used.
    Post-match statistics such as shots, corners, cards, and possession are
    deliberately ignored.
    """
    validate_market_columns(frame)
    result = frame.copy()

    columns: dict[str, list[float | None]] = {
        "AHHomeOpenProb": [],
        "AHAwayOpenProb": [],
        "AHHomeCloseProb": [],
        "AHAwayCloseProb": [],
        "AHHomeSettlement": [],
        "AHAwaySettlement": [],
        "OUOverOpenProb": [],
        "OUUnderOpenProb": [],
        "OUOverCloseProb": [],
        "OUUnderCloseProb": [],
        "OUOverSettlement": [],
        "OUUnderSettlement": [],
    }

    for row in result.to_dict(orient="records"):
        p_home, p_away = _fair_probs(row, "AvgAHH", "AvgAHA")
        p_close_home, p_close_away = _fair_probs(row, "AvgCAHH", "AvgCAHA")

        if p_home is not None:
            home_settle = asian_handicap_settlement(int(row["FTHG"]), int(row["FTAG"]), float(row["AHh"]))
            away_settle = -home_settle
        else:
            home_settle = away_settle = None

        columns["AHHomeOpenProb"].append(p_home)
        columns["AHAwayOpenProb"].append(p_away)
        columns["AHHomeCloseProb"].append(p_close_home)
        columns["AHAwayCloseProb"].append(p_close_away)
        columns["AHHomeSettlement"].append(home_settle)
        columns["AHAwaySettlement"].append(away_settle)

        p_over, p_under = _fair_probs(row, "Avg>2.5", "Avg<2.5")
        p_close_over, p_close_under = _fair_probs(row, "AvgC>2.5", "AvgC<2.5")

        columns["OUOverOpenProb"].append(p_over)
        columns["OUUnderOpenProb"].append(p_under)
        columns["OUOverCloseProb"].append(p_close_over)
        columns["OUUnderCloseProb"].append(p_close_under)
        columns["OUOverSettlement"].append(
            over_under_25_settlement(int(row["FTHG"]), int(row["FTAG"]), True) if p_over is not None else None
        )
        columns["OUUnderSettlement"].append(
            over_under_25_settlement(int(row["FTHG"]), int(row["FTAG"]), False) if p_under is not None else None
        )

    for name, values in columns.items():
        result[name] = values

    # Positive CLV probability means the market moved toward that side after
    # the opening price. This is a diagnostic metric, not a guarantee of profit.
    result["AHHomeCLVProb"] = result["AHHomeCloseProb"] - result["AHHomeOpenProb"]
    result["AHAwayCLVProb"] = result["AHAwayCloseProb"] - result["AHAwayOpenProb"]
    result["OUOverCLVProb"] = result["OUOverCloseProb"] - result["OUOverOpenProb"]
    result["OUUnderCLVProb"] = result["OUUnderCloseProb"] - result["OUUnderOpenProb"]

    return result
