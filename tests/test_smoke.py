from __future__ import annotations

import pandas as pd

from src.data import get_price_data
from src.stats import hedge_ratio, adf_pvalue, half_life
from src.backtest import backtest_pair
from src.eval import metrics


def test_end_to_end_smoke() -> None:
    pairs = ("KO", "PEP")
    px = get_price_data(list(pairs), start="2018-01-01", end="2025-01-01")
    assert not px.empty and all(t in px.columns for t in pairs)

    beta = hedge_ratio(px[pairs[1]], px[pairs[0]])
    spread = px[pairs[1]] - beta * px[pairs[0]]

    # basic stats compute without error
    _ = adf_pvalue(spread)
    _ = half_life(spread)

    results = backtest_pair(
        px[pairs[0]],
        px[pairs[1]],
        beta,
        params={"lookback": 60, "z_in": 2.0, "z_out": 0.5, "stop": 3.5, "cost_bps": 2.0},
    )
    assert {"ret", "equity", "z", "y_pos", "x_pos", "turnover"}.issubset(results.columns)

    m = metrics(results["ret"])  # type: ignore[index]

    # Sanity checks
    assert pd.api.types.is_numeric_dtype(results["ret"]) and len(results) > 100
    assert isinstance(m["sharpe"], float)


