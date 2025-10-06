from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")


def metrics(ret: pd.Series, freq: int = 252) -> dict:
	"""Compute performance metrics from a return series.

	Parameters
	----------
	ret : pd.Series
		Daily strategy returns.
	freq : int, default 252
		Trading days per year for annualization.

	Returns
	-------
	dict
		Dictionary with annualized return, volatility, Sharpe, and max drawdown.
	"""
	r = pd.Series(ret).dropna()
	if r.empty:
		return {"ann_return": 0.0, "ann_vol": 0.0, "sharpe": 0.0, "max_dd": 0.0}

	ann_return = (1 + r).prod() ** (freq / max(len(r), 1)) - 1
	ann_vol = r.std(ddof=1) * np.sqrt(freq)
	sharpe = 0.0 if ann_vol == 0 else ann_return / ann_vol
	equity = (1 + r).cumprod()
	roll_max = equity.cummax()
	drawdown = equity / roll_max - 1.0
	max_dd = drawdown.min()

	return {
		"ann_return": float(ann_return),
		"ann_vol": float(ann_vol),
		"sharpe": float(sharpe),
		"max_dd": float(max_dd),
	}


def plot_equity_curve(ret: pd.Series, ax: plt.Axes | None = None) -> plt.Axes:
	"""Plot equity curve with proper labels and grid."""
	eq = (1 + pd.Series(ret).fillna(0)).cumprod()
	ax = ax or plt.gca()
	ax.plot(eq.index, eq.values, color="#1f77b4", linewidth=2, label="Equity")
	ax.set_title("Equity Curve", fontsize=12)
	ax.set_xlabel("Date")
	ax.set_ylabel("Cumulative Growth (×)")
	ax.legend()
	return ax


def plot_drawdowns(ret: pd.Series, ax: plt.Axes | None = None) -> plt.Axes:
	"""Plot drawdowns over time."""
	eq = (1 + pd.Series(ret).fillna(0)).cumprod()
	roll_max = eq.cummax()
	dd = eq / roll_max - 1.0
	ax = ax or plt.gca()
	ax.fill_between(dd.index, dd.values, 0, color="#d62728", alpha=0.3, label="Drawdown")
	ax.set_title("Drawdowns", fontsize=12)
	ax.set_xlabel("Date")
	ax.set_ylabel("Drawdown")
	ax.legend()
	return ax


def plot_rolling_sharpe(ret: pd.Series, window: int = 126, ax: plt.Axes | None = None) -> plt.Axes:
	"""Plot rolling Sharpe ratio (annualized)."""
	r = pd.Series(ret).fillna(0)
	roll_mean = r.rolling(window).mean()
	roll_std = r.rolling(window).std(ddof=1)
	roll_sharpe = np.where(roll_std == 0, np.nan, (roll_mean / roll_std) * np.sqrt(252))
	ax = ax or plt.gca()
	ax.plot(r.index, roll_sharpe, color="#2ca02c", linewidth=1.8, label="Rolling Sharpe")
	ax.axhline(0.0, color="black", linewidth=0.8)
	ax.set_title(f"Rolling Sharpe ({window}d)", fontsize=12)
	ax.set_xlabel("Date")
	ax.set_ylabel("Sharpe")
	ax.legend()
	return ax


def plot_zscore_with_trades(
	z: pd.Series,
	z_in: float,
	z_out: float,
	stop: float,
	y_pos: pd.Series,
	ax: plt.Axes | None = None,
) -> plt.Axes:
	"""Plot z-score with entry/exit and stop markers from positions.

	Markers are placed on state transitions in `y_pos`.
	"""
	z = pd.Series(z)
	y_pos = pd.Series(y_pos)
	ax = ax or plt.gca()
	ax.plot(z.index, z.values, color="#1f77b4", linewidth=1.5, label="z-score")
	ax.axhline(z_in, color="#ff7f0e", linestyle="--", linewidth=1, label="z_in")
	ax.axhline(-z_in, color="#ff7f0e", linestyle="--", linewidth=1)
	ax.axhline(z_out, color="#2ca02c", linestyle=":", linewidth=1, label="z_out")
	ax.axhline(-z_out, color="#2ca02c", linestyle=":", linewidth=1)
	ax.axhline(stop, color="#d62728", linestyle="-.", linewidth=1, label="stop")
	ax.axhline(-stop, color="#d62728", linestyle="-.", linewidth=1)

	# Transitions
	pos_change = y_pos.fillna(0).diff().fillna(0)
	entries = pos_change != 0
	for t, val in z[entries].items():
		ax.scatter(t, val, s=24, color="#9467bd", marker="o", zorder=5)

	ax.set_title("Z-score with Trades", fontsize=12)
	ax.set_xlabel("Date")
	ax.set_ylabel("z")
	ax.legend()
	return ax
