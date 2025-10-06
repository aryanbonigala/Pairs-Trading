from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from statsmodels.tsa.stattools import adfuller


def hedge_ratio(y: pd.Series, x: pd.Series) -> float:
	"""Estimate the static hedge ratio (beta) of y on x using OLS without intercept.

	The regression is y_t = beta * x_t + e_t (no intercept), commonly used in pairs.

	Parameters
	----------
	y : pd.Series
		Dependent price series.
	x : pd.Series
		Independent price series.

	Returns
	-------
	float
		Estimated hedge ratio beta.
	"""
	aligned = pd.concat([y, x], axis=1, join="inner").dropna()
	if aligned.shape[0] < 2:
		raise ValueError("Not enough overlapping observations to estimate hedge ratio")
	# No intercept: regress y on x directly
	model = OLS(aligned.iloc[:, 0].values, aligned.iloc[:, 1].values)
	result = model.fit()
	beta = float(result.params[0])
	return beta


def adf_pvalue(series: pd.Series) -> float:
	"""Return the ADF test p-value for the null of a unit root.

	Parameters
	----------
	series : pd.Series
		Input time series.

	Returns
	-------
	float
		ADF test p-value.
	"""
	arr = pd.Series(series).dropna().values
	if arr.size < 10:
		raise ValueError("Series too short for ADF test (need >= 10 observations)")
	res = adfuller(arr, autolag="AIC")
	return float(res[1])


def half_life(spread: pd.Series) -> float:
	"""Estimate half-life of mean reversion using an AR(1) approximation.

	We fit the regression: dS_t = phi * S_{t-1} + e_t, where dS_t = S_t - S_{t-1}.
	Then the speed of reversion kappa = -ln(1+phi), and half-life = ln(2)/kappa.

	References: Pairs Trading literature (Ornstein-Uhlenbeck discretization approximation).

	Parameters
	----------
	spread : pd.Series
		Mean-reverting spread series.

	Returns
	-------
	float
		Estimated half-life in days. Returns np.inf if no mean reversion estimated.
	"""
	s = pd.Series(spread).dropna()
	if s.size < 20:
		raise ValueError("Spread too short to estimate half-life (need >= 20 observations)")
	ds = s.diff().dropna()
	lag_s = s.shift(1).dropna()
	aligned = pd.concat([ds, lag_s], axis=1, join="inner").dropna()
	if aligned.empty:
		return float("inf")
	# Regress ds on lagged s, with intercept
	X = add_constant(aligned.iloc[:, 1].values)
	Y = aligned.iloc[:, 0].values
	phi = OLS(Y, X).fit().params[1]
	# Map to OU speed of reversion
	kappa = -np.log1p(phi)
	if kappa <= 0:
		return float("inf")
	return float(np.log(2.0) / kappa)
