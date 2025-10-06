from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data import get_price_data
from src.stats import hedge_ratio, adf_pvalue, half_life
from src.backtest import backtest_pair
from src.eval import metrics


def main() -> None:
	pairs = ("KO", "PEP")
	px = get_price_data(list(pairs), start="2018-01-01", end="2025-01-01")
	assert not px.empty and all(t in px.columns for t in pairs)

	beta = hedge_ratio(px[pairs[1]], px[pairs[0]])
	spread = px[pairs[1]] - beta * px[pairs[0]]
	print({
		"beta": beta,
		"adf_pvalue": adf_pvalue(spread),
		"half_life": half_life(spread),
	})

	results = backtest_pair(
		px[pairs[0]], px[pairs[1]], beta,
		params={"lookback": 60, "z_in": 2.0, "z_out": 0.5, "stop": 3.5, "cost_bps": 2.0},
	)
	assert set(["ret", "equity", "z", "y_pos", "x_pos", "turnover"]).issubset(results.columns)

	m = metrics(results["ret"])
	print("metrics:", m)

	# Basic sanity checks
	assert pd.api.types.is_numeric_dtype(results["ret"]) and len(results) > 100
	assert isinstance(m["sharpe"], float)


if __name__ == "__main__":
	main()
