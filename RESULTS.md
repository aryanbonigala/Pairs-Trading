## How to Read

- Each row is one experiment. Timeframe and start equity apply per-pair unless noted.
- Config(s): key strategy settings. LB = lookback; z_in/z_out = entry/exit z-score thresholds; stop in z; cost_bps per-leg.
- Aggregate Results: averages across pairs (when multi-pair). WR = win rate (share of pairs with positive P&L).
- ADF p: Augmented Dickey-Fuller p-value on spread; lower implies stronger stationarity. Half-life estimates mean-reversion speed.
- P&L and Final Equity are per pair with $100k starting equity; not a portfolio sum unless specified.

## Test Results Summary

### T1 — KO–PEP smoke test (single pair)
- **Timeframe**: 2018-01-01 to 2025-01-01
- **Start Equity**: $100,000 per pair
- **Universe**:
  - KO–PEP
- **Config (baseline)**:
  - lookback: 60
  - z_in: 2.0
  - z_out: 0.5
  - stop: 3.5
  - cost_bps: 2.0
- **Key Results**:
  - beta: 2.7133
  - Total P&L: -$5,452.84
  - Final Equity: $94,547.16
  - ann_return: -3.43%
  - ann_vol: 28.36%
  - Sharpe: -0.121
  - max_dd: -55.25%
- **Notes**: Poor mean reversion (ADF p≈0.31), half-life ~109 days.

### T2 — Multi-pair baseline scan
- **Timeframe**: 2018-01-01 to 2025-01-01
- **Start Equity**: $100,000 per pair
- **Universe**:
  - AAPL–MSFT
  - GOOGL–META
  - CSCO–JNPR
  - KO–PEP
  - PG–CL
  - F–GM
  - NKE–ADDYY
  - PM–MO
  - XOM–CVX
  - SLB–HAL
- **Config (baseline)**:
  - lookback: 60
  - z_in: 2.0
  - z_out: 0.5
  - stop: 3.5
  - cost_bps: 2.0
- **Aggregate Results**:
  - positives: 5
  - negatives: 4
  - errors: 1 (JNPR data)
  - examples: AAPL–MSFT +$1,116.98; F–GM +$39,858.16; XOM–CVX +$21,210.69
- **Notes**: Majority positive; KO–PEP and PG–CL weak; JNPR unavailable.

### T3 — Enhanced entries: take-profit + confirmation; templates
- **Timeframe**: 2018-01-01 to 2025-01-01
- **Start Equity**: $100,000 per pair
- **Universe**:
  - same 10 pairs as T2
- **Configs**:
  - baseline
  - slow:
    - lookback: 90
    - z_in: 2.5
    - z_out: 0.5
    - stop: 4.0
    - tp: 0.1
    - confirm: 0.1
  - slow_strict:
    - lookback: 126
    - z_in: 3.0
    - z_out: 0.5
    - stop: 4.0
    - tp: 0.0
    - confirm: 0.1
  - fast:
    - lookback: 45
    - z_in: 2.0
    - z_out: 0.4
    - stop: 3.5
    - tp: 0.1
    - confirm: 0.1
- **Aggregate Results**:
  - baseline avg P&L: $6,967 (WR 66.7%)
  - slow avg P&L: $8,931 (WR 66.7%)
  - slow_strict avg P&L: $3,840 (WR 55.6%)
  - fast avg P&L: $12,107 (WR 66.7%)
- **Notes**: Fast best overall; slow/strict reduced losses on staples; KO–PEP improved under slow_strict.

### T4 — Dynamic sizing + vol targeting (10% ann, cap 1.5)
- **Timeframe**: 2018-01-01 to 2025-01-01
- **Start Equity**: $100,000 per pair
- **Universe**:
  - same 10 pairs as T2
- **Config (dynamic)**:
  - size rule: min(|z|/z_in, 1.5)
  - vol_target: 10% (window 63)
  - costs: cost_bps as baseline
- **Aggregate Results**:
  - baseline avg P&L: $6,967 (WR 66.7%)
  - fast avg P&L: $12,107 (WR 66.7%)
  - dynamic avg P&L: $5,537 (WR 55.6%), median $486
- **Notes**: Reduced upside on strong pairs (e.g., NKE–ADDYY), modest tail improvement (e.g., SLB–HAL).

### T5 — Dynamic sizing + regime filters; higher vol target/cap by sector
- **Timeframe**: 2018-01-01 to 2025-01-01
- **Start Equity**: $100,000 per pair
- **Universe**:
  - same 10 pairs as T2
- **Config (dynamic_filtered)**:
  - vol_target (ann): energy 15%, autos 14%, consumer 13%, tech 12%, tobacco 12%, staples 10%
  - cap: 2.0
  - signal template: fast
  - regime filter: rolling 252d ADF p < 0.1 AND half-life ∈ [10, 75]
- **Aggregate Results**:
  - baseline avg P&L: $6,967; fast avg P&L: $12,107
  - dynamic_filtered avg P&L: $1,452; median $1,191; WR 66.7%
- **Notes**: Improved weak pairs (KO–PEP to small gain; PG–CL to ~breakeven), but underperformed fast on strong pairs (XOM–CVX, PM–MO) due to conservative filtering and caps.

Notes:
- All tests assume dollar-neutral positions, share-and-price-delta P&L with transaction costs applied on traded notional.
- Each backtest was run independently with $100k per pair; results are not portfolio-aggregated unless stated.
- CSCO–JNPR failed in T2/T3/T4/T5 due to JNPR data unavailability via yfinance in the tested period.
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
