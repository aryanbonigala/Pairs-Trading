# Backtest Results Log

This document tracks every backtest we run, with parameters and performance. Keep entries short and consistent so the list stays readable.

## How to read this
- **Timeframe**: inclusive start and end dates used for prices
- **Start Equity**: initial notional for P/L computation (paper dollars)
- **Params**: {lookback, z_in, z_out, stop, cost_bps}
- **P/L**: ending equity − start equity (paper dollars)
- **Max DD**: maximum peak-to-trough drawdown on equity (%)
- **Sharpe**: annualized using daily returns (sqrt(252))
- **Turnover**: average daily gross turnover (%)

## Results

| Date Run | Pair(s) | Timeframe | Start Equity | Params | Total P/L | CAGR | Sharpe | Max DD | Trades | Turnover | Notes |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| 2025-10-06 | KO–PEP | 2018-01-01 → 2025-01-01 | 100,000 | {60, 2.0, 0.5, 3.5, 2.0} | TBD | TBD | TBD | TBD | TBD | TBD | Smoke-test defaults |

## Add a new run
1) Run your backtest in  or via code.
2) Compute metrics with  and record values.
3) Append a new row to the table above with your numbers.

### Template row (copy/paste)
| YYYY-MM-DD | TICKER_A–TICKER_B | YYYY-MM-DD → YYYY-MM-DD | 100,000 | {60, 2.0, 0.5, 3.5, 2.0} | 0 | 0.0% | 0.00 | 0.0% | 0 | 0.0% | brief note |
