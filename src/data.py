from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(tickers: List[str], start: str, end: str) -> Path:
	"""Return a deterministic cache path for the ticker basket and date range.

	Parameters
	----------
	tickers : list[str]
		List of ticker symbols.
	start : str
		Start date in YYYY-MM-DD format.
	end : str
		End date in YYYY-MM-DD format.

	Returns
	-------
	Path
		Path to the cache CSV under `data/`.
	"""
	slug = "_".join(sorted([t.replace("/", "-") for t in tickers]))
	return DATA_DIR / f"adjclose_{slug}_{start}_{end}.csv"


def _validate_dates(start: str, end: str) -> tuple[datetime, datetime]:
	"""Validate and parse date strings.

	Raises a ValueError if dates are invalid or end < start.
	"""
	start_dt = datetime.fromisoformat(start)
	end_dt = datetime.fromisoformat(end)
	if end_dt < start_dt:
		raise ValueError("end date must be on/after start date")
	return start_dt, end_dt


def _clean_price_frame(df: pd.DataFrame) -> pd.DataFrame:
	"""Forward/back-fill minor gaps and drop all-NaN columns.

	- Ensures index is DatetimeIndex, sorted, and tz-naive
	- Drops duplicate index entries
	- Fills small gaps using ffill then bfill
	- Drops columns that remain all-NaN after filling
	"""
	if not isinstance(df.index, pd.DatetimeIndex):
		df.index = pd.to_datetime(df.index)
	if df.index.tz is not None:
		df.index = df.index.tz_convert(None)
	df = df[~df.index.duplicated(keep="first")]
	df = df.sort_index()
	# Light-touch fill; do not fabricate long spans
	df = df.ffill(limit=5).bfill(limit=2)
	# Remove columns that are still entirely NaN
	df = df.dropna(axis=1, how="all")
	return df


def get_price_data(tickers: List[str], start: str, end: str) -> pd.DataFrame:
	"""Download daily Adjusted Close prices and cache to `data/`.

	This function fetches adjusted close prices for the provided tickers from
	yfinance, caches them as a CSV in `data/`, and performs light cleaning to
	handle small gaps. If a cache file matching the request exists, it is loaded
	to avoid repeated downloads.

	Parameters
	----------
	tickers : list[str]
		List of ticker symbols (e.g., ["KO", "PEP"]).
	start : str
		Start date in YYYY-MM-DD format.
	end : str
		End date in YYYY-MM-DD format.

	Returns
	-------
	pd.DataFrame
		DataFrame of Adjusted Close prices with `DatetimeIndex` and columns as tickers.
	"""
	if not tickers:
		raise ValueError("tickers must be a non-empty list")
	_validate_dates(start, end)
	cache_file = _cache_path(tickers, start, end)

	if cache_file.exists():
		try:
			df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
			return _clean_price_frame(df)
		except Exception:
			# Fallback to re-download if cache is corrupted
			pass

	# Download with yfinance
	data = yf.download(
		tickers=tickers,
		start=start,
		end=end,
		interval="1d",
		auto_adjust=False,
		progress=False,
		threads=True,
	)

	# yfinance returns a MultiIndex columns when multiple tickers
	if isinstance(data.columns, pd.MultiIndex):
		adj = data.get(("Adj Close"))
		if adj is None:
			# some tickers may not have Adj Close; fall back to Close
			adj = data.get(("Close"))
			if adj is None:
				raise RuntimeError("Downloaded data missing Adj Close and Close")
		adj.columns.name = None
		prices = adj.astype(float)
	else:
		# Single ticker path; prefer Adj Close else Close
		if "Adj Close" in data.columns:
			prices = data["Adj Close"].to_frame(name=tickers[0]).astype(float)
		elif "Close" in data.columns:
			prices = data["Close"].to_frame(name=tickers[0]).astype(float)
		else:
			raise RuntimeError("Downloaded data missing Adj Close and Close")

	prices = _clean_price_frame(prices)

	# Ensure only requested tickers in order; drop missing tickers gracefully
	present = [t for t in tickers if t in prices.columns]
	missing = sorted(set(tickers) - set(present))
	if missing:
		# Keep going but notify via warning
		print(f"Warning: missing tickers with no data: {missing}")
	prices = prices.reindex(columns=present)

	# Persist cache
	try:
		prices.to_csv(cache_file)
	except Exception:
		# Non-fatal if cache cannot be written
		pass

	return prices
