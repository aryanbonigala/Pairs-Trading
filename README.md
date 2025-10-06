# Pairs Trading Strategy (Python)

A clean, modular, and production-ready pairs trading project suitable for a quant internship portfolio. The repository includes data ingestion with caching, statistical utilities (hedge ratio, ADF, half-life), signal generation, a vectorized backtester with costs, and professional evaluation plots and metrics.

## Features
- Modular `src/` package with type hints and docstrings
- Cached price downloads using `yfinance`
- Hedge ratio via OLS (no intercept), ADF p-value, half-life
- Z-score based trading rules (entry/exit/stop) with dollar-neutral positions
- Vectorized backtester with transaction costs and turnover
- Metrics and plots (equity, drawdowns, rolling Sharpe, z-score with trade markers)
- Four notebooks demonstrating end-to-end workflow

## Project Structure
```
pairs-trading/
├─ data/
│  ├─ raw/                     # cached raw CSV price data
│  ├─ processed/               # derived/intermediate datasets (ignored)
│  └─ interim/                 # temporary artifacts (ignored)
├─ notebooks/
│  ├─ 01_data_download.ipynb
│  ├─ 02_cointegration_scan.ipynb
│  ├─ 03_backtest.ipynb
│  └─ 04_results_report.ipynb
├─ src/
│  ├─ data.py                  # price data fetch + clean
│  ├─ stats.py                 # hedge ratio, cointegration, half-life
│  ├─ signals.py               # z-score & trading rules
│  ├─ backtest.py              # vectorized backtester
│  ├─ eval.py                  # metrics & plots
├─ requirements.txt
└─ README.md
```

## Setup
1. Create environment (Python 3.10+ recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Optional: enable Jupyter extensions if using VS Code or classic Jupyter.

## Usage
### Notebook 1 — Data Download
```python
from src.data import get_price_data

tickers = ["KO", "PEP", "XOM", "CVX"]
px = get_price_data(tickers, start="2018-01-01", end="2025-01-01")
px.head()
```

### Notebook 2 — Cointegration Scan and Stats
```python
from src.stats import hedge_ratio, adf_pvalue, half_life

beta = hedge_ratio(px["PEP"], px["KO"])
spread = px["PEP"] - beta * px["KO"]
print("ADF p-value:", adf_pvalue(spread))
print("Half-life:", half_life(spread))
```

### Notebook 3 — Backtest
```python
from src.backtest import backtest_pair

results = backtest_pair(
	px["KO"], px["PEP"], beta,
	params={"lookback": 60, "z_in": 2.0, "z_out": 0.5, "stop": 3.5, "cost_bps": 2.0}
)
results.tail()
```

### Notebook 4 — Evaluation
```python
from src.eval import metrics, plot_equity_curve, plot_drawdowns, plot_rolling_sharpe, plot_zscore_with_trades

m = metrics(results["ret"])  # daily returns
print(m)

import matplotlib.pyplot as plt
fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
plot_equity_curve(results["ret"], ax=axes[0])
plot_drawdowns(results["ret"], ax=axes[1])
plot_rolling_sharpe(results["ret"], ax=axes[2])
plt.tight_layout()
plt.show()

fig, ax = plt.subplots(figsize=(10, 4))
plot_zscore_with_trades(
	z=results["z"], z_in=2.0, z_out=0.5, stop=3.5, y_pos=results["y_pos"], ax=ax
)
plt.tight_layout(); plt.show()
```

## Notes
- Data is cached under `data/raw/` by ticker basket and date range.
- If some tickers fail to download, they are reported and omitted gracefully.
- Transaction costs are assessed on position changes (per-leg bps).
- All modules are PEP8-compliant and include type hints.

## Optional Dashboard
You can build a Streamlit dashboard on top of this package:
```bash
streamlit run app.py
```
(Left as an exercise; consider interactive pair selection, parameter sliders, and live plots.)

## License
MIT
