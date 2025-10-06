from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def zscore(spread: pd.Series, lookback: int) -> pd.Series:
	"""Compute rolling z-score of a spread.

	z_t = (S_t - mean_{t-L+1..t}(S)) / std_{t-L+1..t}(S)

	Parameters
	----------
	spread : pd.Series
		Spread series (e.g., y - beta * x).
	lookback : int
		Rolling window length for mean and std.

	Returns
	-------
	pd.Series
		Rolling z-score with NaNs for the warm-up period.
	"""
	s = pd.Series(spread).astype(float)
	mu = s.rolling(lookback, min_periods=lookback).mean()
	sigma = s.rolling(lookback, min_periods=lookback).std(ddof=1)
	z = (s - mu) / sigma
	return z


def generate_positions(
	z: pd.Series,
	beta: float,
	z_in: float,
	z_out: float,
	stop: float,
	tp_threshold: float | None = None,
	confirm_delta: float = 0.0,
) -> tuple[pd.Series, pd.Series]:
	"""Generate dollar-neutral positions for a pair based on z-score rules.

	Trading rules:
	- Enter when |z| >= z_in, with optional reversion confirmation: enter only after
	  z turns back toward 0 by at least `confirm_delta` following a threshold cross.
	- Exit when |z| <= z_out
	- Stop when |z| >= stop (in absolute value)
	- Optional take-profit: if in position and |z| < tp_threshold, flatten

	Long spread (z < -z_in): long y, short x*beta
	Short spread (z >  z_in): short y, long x*beta

	Positions are scaled to 1 dollar notional on y leg; x leg is encoded as
	absolute short notional via `x_pos = beta * y_pos` (PnL subtracts x leg).

	Parameters
	----------
	z : pd.Series
		Z-score series for the spread.
	beta : float
		Hedge ratio (y on x).
	z_in : float
		Entry threshold for absolute z.
	z_out : float
		Exit threshold for absolute z.
	stop : float
		Stop-out threshold for absolute z.
	tp_threshold : float | None
		Optional take-profit threshold on |z| (e.g., 0.0–0.2). If None, disabled.
	confirm_delta : float
		Require that z reverses by at least this amount toward 0 after first
		crossing z_in before entering. 0 disables confirmation.

	Returns
	-------
	tuple[pd.Series, pd.Series]
		(y_position, x_position) series with values in {-1, 0, 1} scaled as
		dollar-neutral via beta on x leg.
	"""
	z = pd.Series(z).copy()
	abs_z = z.abs()

	# State machine: -1 short spread, 0 flat, +1 long spread
	state = np.zeros(len(z), dtype=int)
	pending_entry = None  # None or ('short'|'long', z_at_cross)

	in_pos = False
	pos = 0
	for i in range(len(z)):
		zi = z.iat[i]
		if np.isnan(zi):
			state[i] = 0 if not in_pos else pos
			continue

		if in_pos:
			# Stop first
			if abs(zi) >= stop:
				in_pos = False
				pos = 0
				pending_entry = None
				state[i] = 0
				continue
			# Take-profit
			if tp_threshold is not None and abs(zi) < tp_threshold:
				in_pos = False
				pos = 0
				pending_entry = None
				state[i] = 0
				continue
			# Exit
			if abs(zi) <= z_out:
				in_pos = False
				pos = 0
				pending_entry = None
				state[i] = 0
				continue
			# Maintain
			state[i] = pos
			continue

		# Flat logic
		if pending_entry is None:
			# Watch for threshold cross
			if zi >= z_in:
				pending_entry = ("short", zi)
				state[i] = 0
				continue
			elif zi <= -z_in:
				pending_entry = ("long", zi)
				state[i] = 0
				continue
			else:
				state[i] = 0
				continue
		else:
			# Confirmation: require reversal toward 0 by confirm_delta
			kind, z_cross = pending_entry
			if confirm_delta <= 0:
				# immediate entry on cross
				in_pos = True
				pos = -1 if kind == "short" else 1
				pending_entry = None
				state[i] = pos
				continue
			else:
				if kind == "short":
					# need zi <= z_cross - confirm_delta (move toward 0 from positive side)
					if zi <= max(z_in, z_cross - confirm_delta):
						in_pos = True
						pos = -1
						pending_entry = None
						state[i] = pos
						continue
				elif kind == "long":
					# need zi >= z_cross + confirm_delta (move toward 0 from negative side)
					if zi >= min(-z_in, z_cross + confirm_delta):
						in_pos = True
						pos = 1
						pending_entry = None
						state[i] = pos
						continue
				# Still pending
				state[i] = 0
				continue

	state_series = pd.Series(state, index=z.index)
	# y position: +1 for long spread, -1 for short spread
	y_pos = state_series.astype(float)
	# x position: scaled by +beta and interpreted as a short exposure in PnL
	x_pos = beta * y_pos
	return y_pos, x_pos
