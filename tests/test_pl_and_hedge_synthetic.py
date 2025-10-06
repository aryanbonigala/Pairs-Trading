from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest import backtest_pair
from src.eval import metrics


def test_pl_and_hedge_synthetic() -> None:
	# Deterministic RNG
	rng = np.random.default_rng(42)
	n = 1500

	# Synthetic x: geometric random walk
	dx = 0.0005 + 0.01 * rng.standard_normal(n)
	x = 100 * np.exp(np.cumsum(dx))

	# Synthetic spread: AR(1) mean-reverting
	phi = 0.95
	sigma_eps = 0.5
	eps = sigma_eps * rng.standard_normal(n)
	spread = np.zeros(n)
	for t in range(1, n):
		spread[t] = phi * spread[t - 1] + eps[t]

	# Construct y = beta * x + spread
	beta = 1.5
	y = beta * x + spread

	index = pd.date_range("2018-01-01", periods=n, freq="B")
	pxA = pd.Series(x, index=index, name="A")
	pxB = pd.Series(y, index=index, name="B")

	res = backtest_pair(
		pricesA=pxA,
		pricesB=pxB,
		beta=beta,
		params={"lookback": 60, "z_in": 1.5, "z_out": 0.5, "stop": 4.0, "cost_bps": 0.5},
	)

	# Enough observations
	non_na = res["ret"].dropna()
	assert len(non_na) >= 500

	# Turnover
	assert res["turnover"].sum() > 0

	# Dollar-neutrality residual
	hedge_residual = res["y_pos"] + res["x_pos"] / (-beta)
	assert float(hedge_residual.abs().mean()) < 1e-8

	# Profitability
	m = metrics(res["ret"])
	assert m["sharpe"] > 0.5
	start_capital = 100_000
	final_equity = start_capital * res["equity"].iloc[-1]
	total_pnl = final_equity - start_capital
	assert total_pnl > 0
