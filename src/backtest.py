from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from .signals import zscore, generate_positions


@dataclass
class BacktestParams:
	lookback: int = 60
	z_in: float = 2.0
	z_out: float = 0.5
	stop: float = 3.5
	cost_bps: float = 1.0  # per leg per trade, in basis points


def _compute_turnover(weight: pd.Series) -> pd.Series:
	"""Compute daily turnover as absolute day-over-day change in weight."""
	return weight.fillna(0.0).diff().abs()


def backtest_pair(
	pricesA: pd.Series,
	pricesB: pd.Series,
	beta: float,
	params: Dict,
) -> pd.DataFrame:
	"""Backtest a pairs strategy on two price series.

	This function constructs the spread S = B - beta * A, computes its z-score,
	and generates positions following threshold rules. It then computes daily PnL
	using dollar-neutral weights and applies transaction costs.

	Parameters
	----------
	pricesA : pd.Series
		Price series for asset A (x in hedge ratio, the independent leg).
	pricesB : pd.Series
		Price series for asset B (y in hedge ratio, the dependent leg).
	beta : float
		Hedge ratio such that spread = B - beta * A.
	params : dict
		Parameters dict with keys: lookback, z_in, z_out, stop, cost_bps.

	Returns
	-------
	pd.DataFrame
		Columns: ret, equity, z, y_pos, x_pos, turnover.
	"""
	index = pd.Index(sorted(pricesA.dropna().index.intersection(pricesB.dropna().index)))
	pxA = pricesA.reindex(index).astype(float)
	pxB = pricesB.reindex(index).astype(float)

	spread = pxB - beta * pxA
	lookback = int(params.get("lookback", 60))
	z = zscore(spread, lookback=lookback)
	y_pos, x_pos = generate_positions(
		z=z,
		beta=beta,
		z_in=float(params.get("z_in", 2.0)),
		z_out=float(params.get("z_out", 0.5)),
		stop=float(params.get("stop", 3.5)),
	)

	# Share quantities (previous close holdings)
	qB = y_pos.shift(1).fillna(0.0)
	# x_pos encodes absolute short notional in units of shares equivalent to beta*y_pos
	qA = -x_pos.shift(1).fillna(0.0)

	# Price changes
	dB = pxB.diff().fillna(0.0)
	dA = pxA.diff().fillna(0.0)

	# Dollar PnL
	pnl = (qB * dB) + (qA * dA)

	# Prior-day gross exposure (denominator for returns)
	gross_exposure_prev = (qB.abs() * pxB.shift(1).fillna(method="ffill") + qA.abs() * pxA.shift(1).fillna(method="ffill"))
	gross_exposure_prev = gross_exposure_prev.replace(0.0, np.nan)

	# Transaction costs on traded notional
	cost_bps = float(params.get("cost_bps", 1.0))
	dqB = y_pos.diff().abs().fillna(0.0)
	dqA = x_pos.diff().abs().fillna(0.0)
	traded_notional = (dqB * pxB) + (dqA * pxA)
	cost = (cost_bps / 1e4) * (traded_notional / gross_exposure_prev).fillna(0.0)

	# Returns normalized by prior-day gross exposure
	gross_ret = (pnl / gross_exposure_prev).fillna(0.0)
	ret = gross_ret - cost
	equity = (1.0 + ret).cumprod()

	out = pd.DataFrame(
		{
			"ret": ret,
			"equity": equity,
			"z": z,
			"y_pos": y_pos,
			"x_pos": x_pos,
			"turnover": (traded_notional / gross_exposure_prev).fillna(0.0),
		}
	)
	return out
