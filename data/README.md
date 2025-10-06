# Data Directory

- raw/: cached raw CSV price data written by `src.data.get_price_data`
- processed/: derived/intermediate datasets you create during analysis (gitignored)
- interim/: temporary artifacts (gitignored)

Notes:
- Cache filenames follow: `adjclose_{TICKER1_..._TICKERN}_{START}_{END}.csv`
- You can safely delete files in `raw/`; they will be re-created on next run.
