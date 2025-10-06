from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data import get_price_data
from src.stats import hedge_ratio
from src.backtest import backtest_pair


@pytest.mark.slow
def test_pl_and_hedge_integration(internet_and_yfinance: bool) -> None:
	# Attempt download; skip cleanly on failure
	try:
		px = get_price_data(["KO", "PEP"], start="2018-01-01", end="2024-12-31")
	except Exception as e:
		pytest.skip(f"Download failed: {e}")

	# Data integrity
	assert {"KO", "PEP"}.issubset(px.columns)
	assert len(px) >= 500

	beta = hedge_ratio(px["PEP"], px["KO"])
	assert np.isfinite(beta) and beta > 0

	res = backtest_pair(
		px["KO"], px["PEP"], beta,
		params={"lookback": 60, "z_in": 2.0, "z_out": 0.5, "stop": 3.5, "cost_bps": 2.0},
	)

	# After warmup, no NaNs in ret/equity
	valid = res.dropna(subset=["ret", "equity"]).index
	assert len(valid) >= 500
	assert res.loc[valid, ["ret", "equity"]].isna().sum().sum() == 0

	# Turnover > 0
	assert res["turnover"].sum() > 0

	# Dollar-neutrality residual
	hedge_residual = res["y_pos"] + res["x_pos"] / (-beta)
	assert float(hedge_residual.abs().mean()) < 1e-8

	# Report P/L
	start_capital = 100_000
	daily_pnl = start_capital * res["ret"].fillna(0)
	final_equity = start_capital * res["equity"].iloc[-1]
	total_pnl = final_equity - start_capital
	print(f"Total P&L: ${total_pnl:,.2f} | Final Equity: ${final_equity:,.2f}")
