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


def prepare_market_baseline(frame: pd.DataFrame) -> pd.DataFrame:
    """Create pre-match market probabilities and realized settlements.

    Only opening/closing prices, match identity, and final result are used.
    Post-match statistics such as shots, corners, cards, and possession are
    deliberately ignored.
    """
    validate_market_columns(frame)
    result = frame.copy()

    ah_home_open_prob: list[float | None] = []
    ah_away_open_prob: list[float | None] = []
    ah_home_close_prob: list[float | None] = []
    ah_away_close_prob: list[float | None] = []
    ah_home_settlement: list[float | None] = []
    ah_away_settlement: list[float | None] = []

    ou_over_open_prob: list[float | None] = []
    ou_under_open_prob: list[float | None] = []
    ou_over_close_prob: list[float | None] = []
    ou_under_close_prob: list[float | None] = []
    ou_over_settlement: list[float | None] = []
    ou_under_settlement: list[float | None] = []

    for row in result.itertuples(index=False):
        # Asian Handicap opening market.
        if all(_valid_odds(getattr(row, c)) for c in ("AvgAHH", "AvgAHA")):
            p_home, p_away = fair_two_way_probability(float(row.AvgAHH), float(row.AvgAHA))
        else:
            p_home = p_away = None

        # Closing AH fields are optional because some older files use a
        # different schema. They are only calculated when all fields exist.
        if all(hasattr(row, c) and _valid_odds(getattr(row, c)) for c in ("AvgCAHH", "AvgCAHA")):
            p_close_home, p_close_away = fair_two_way_probability(float(row.AvgCAHH), float(row.AvgCAHA))
        else:
            p_close_home = p_close_away = None

        if p_home is not None:
            home_settle = asian_handicap_settlement(int(row.FTHG), int(row.FTAG), float(row.AHh))
            away_settle = -home_settle
        else:
            home_settle = away_settle = None

        ah_home_open_prob.append(p_home)
        ah_away_open_prob.append(p_away)
        ah_home_close_prob.append(p_close_home)
        ah_away_close_prob.append(p_close_away)
        ah_home_settlement.append(home_settle)
        ah_away_settlement.append(away_settle)

        # O/U 2.5 opening market.
        if all(_valid_odds(getattr(row, c)) for c in ("Avg>2.5", "Avg<2.5")):
            p_over, p_under = fair_two_way_probability(float(row._asdict()["Avg>2.5"]), float(row._asdict()["Avg<2.5"]))
        else:
            p_over = p_under = None

        if all(hasattr(row, c) and _valid_odds(getattr(row, c)) for c in ("AvgC>2.5", "AvgC<2.5")):
            p_close_over, p_close_under = fair_two_way_probability(
                float(row._asdict()["AvgC>2.5"]), float(row._asdict()["AvgC<2.5"])
            )
        else:
            p_close_over = p_close_under = None

        ou_over_open_prob.append(p_over)
        ou_under_open_prob.append(p_under)
        ou_over_close_prob.append(p_close_over)
        ou_under_close_prob.append(p_close_under)
        ou_over_settlement.append(over_under_25_settlement(int(row.FTHG), int(row.FTAG), True) if p_over is not None else None)
        ou_under_settlement.append(over_under_25_settlement(int(row.FTHG), int(row.FTAG), False) if p_under is not None else None)

    result["AHHomeOpenProb"] = ah_home_open_prob
    result["AHAwayOpenProb"] = ah_away_open_prob
    result["AHHomeCloseProb"] = ah_home_close_prob
    result["AHAwayCloseProb"] = ah_away_close_prob
    result["AHHomeSettlement"] = ah_home_settlement
    result["AHAwaySettlement"] = ah_away_settlement
    result["OUOverOpenProb"] = ou_over_open_prob
    result["OUUnderOpenProb"] = ou_under_open_prob
    result["OUOverCloseProb"] = ou_over_close_prob
    result["OUUnderCloseProb"] = ou_under_close_prob
    result["OUOverSettlement"] = ou_over_settlement
    result["OUUnderSettlement"] = ou_under_settlement

    # Positive CLV probability means the market moved toward that side after
    # the opening price. This is a diagnostic metric, not a guarantee of profit.
    result["AHHomeCLVProb"] = result["AHHomeCloseProb"] - result["AHHomeOpenProb"]
    result["AHAwayCLVProb"] = result["AHAwayCloseProb"] - result["AHAwayOpenProb"]
    result["OUOverCLVProb"] = result["OUOverCloseProb"] - result["OUOverOpenProb"]
    result["OUUnderCLVProb"] = result["OUUnderCloseProb"] - result["OUUnderOpenProb"]

    return result
