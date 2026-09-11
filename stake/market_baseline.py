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


def _valid_ah_line(value: object) -> bool:
    try:
        line = float(value)
        if not math.isfinite(line):
            return False
        quarter_units = round(line * 4)
        return abs(line * 4 - quarter_units) <= 1e-9
    except (TypeError, ValueError):
        return False


def _fair_probs(row: dict[str, object], first: str, second: str) -> tuple[float | None, float | None]:
    if not (_valid_odds(row.get(first)) and _valid_odds(row.get(second))):
        return None, None
    return fair_two_way_probability(float(row[first]), float(row[second]))


def _profit_from_settlement(settlement: float, odds: float) -> float:
    """Return profit on a 1-unit bet from an AH/O-U settlement.

    A full/half win earns the corresponding fraction of (odds - 1).
    A push earns zero and a full/half loss loses the corresponding fraction
    of the stake. This preserves Asian quarter-line settlement exactly.
    """
    if settlement > 0:
        return settlement * (odds - 1.0)
    return settlement


def prepare_market_baseline(frame: pd.DataFrame) -> pd.DataFrame:
    """Create pre-match market prices and realized settlements.

    Only opening/closing prices, match identity, and final result are used.
    Post-match statistics such as shots, corners, cards, and possession are
    deliberately ignored. Missing market observations remain missing.

    Asian Handicap outcomes are retained as continuous settlements rather
    than being coerced into binary wins. This preserves pushes, half-wins,
    and half-losses for quarter-goal lines.
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
        "AHHomeOpenProfit": [],
        "AHAwayOpenProfit": [],
        "OUOverOpenProb": [],
        "OUUnderOpenProb": [],
        "OUOverCloseProb": [],
        "OUUnderCloseProb": [],
        "OUOverSettlement": [],
        "OUUnderSettlement": [],
        "OUOverOpenProfit": [],
        "OUUnderOpenProfit": [],
    }

    for row in result.to_dict(orient="records"):
        p_home, p_away = _fair_probs(row, "AvgAHH", "AvgAHA")
        p_close_home, p_close_away = _fair_probs(row, "AvgCAHH", "AvgCAHA")

        if p_home is not None and _valid_ah_line(row.get("AHh")):
            home_settle = asian_handicap_settlement(
                int(row["FTHG"]), int(row["FTAG"]), float(row["AHh"])
            )
            away_settle = -home_settle
            home_profit = _profit_from_settlement(home_settle, float(row["AvgAHH"]))
            away_profit = _profit_from_settlement(away_settle, float(row["AvgAHA"]))
        else:
            home_settle = away_settle = None
            home_profit = away_profit = None

        columns["AHHomeOpenProb"].append(p_home)
        columns["AHAwayOpenProb"].append(p_away)
        columns["AHHomeCloseProb"].append(p_close_home)
        columns["AHAwayCloseProb"].append(p_close_away)
        columns["AHHomeSettlement"].append(home_settle)
        columns["AHAwaySettlement"].append(away_settle)
        columns["AHHomeOpenProfit"].append(home_profit)
        columns["AHAwayOpenProfit"].append(away_profit)

        p_over, p_under = _fair_probs(row, "Avg>2.5", "Avg<2.5")
        p_close_over, p_close_under = _fair_probs(row, "AvgC>2.5", "AvgC<2.5")

        over_settle = (
            over_under_25_settlement(int(row["FTHG"]), int(row["FTAG"]), True)
            if p_over is not None
            else None
        )
        under_settle = (
            over_under_25_settlement(int(row["FTHG"]), int(row["FTAG"]), False)
            if p_under is not None
            else None
        )

        columns["OUOverOpenProb"].append(p_over)
        columns["OUUnderOpenProb"].append(p_under)
        columns["OUOverCloseProb"].append(p_close_over)
        columns["OUUnderCloseProb"].append(p_close_under)
        columns["OUOverSettlement"].append(over_settle)
        columns["OUUnderSettlement"].append(under_settle)
        columns["OUOverOpenProfit"].append(
            _profit_from_settlement(over_settle, float(row["Avg>2.5"])) if over_settle is not None else None
        )
        columns["OUUnderOpenProfit"].append(
            _profit_from_settlement(under_settle, float(row["Avg<2.5"])) if under_settle is not None else None
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
