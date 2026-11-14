# polymarket-faa-attribution-02

Quantile forecasts for Polymarket Yes prices on how the November 2026 FAA
outage will officially be attributed. For each market and each of the 240
minutes after the checkpoint, `main.py` writes five quantiles (5%, 25%,
50%, 75%, 95%) of that minute's price.

## Model

- **Centre:** the last observed price. These markets barely move most of
  the time, so persistence is the best guess for the median.
- **Spread:** learned per market, not fixed. Take the absolute price moves
  over one-hour stretches across the trailing 24 hours, take their median,
  and rescale it (median absolute deviation to a standard deviation) into
  a per-minute volatility, floored at 0.0005 and capped at 0.0025.
- **Quantiles:** centre plus the normal z-score for each level times the
  volatility times the square root of the minutes ahead, clamped to
  [0, 1] and rounded to six decimals.

Practice backtest: pinball loss about 0.0029, against about 0.0036 for a
fixed-spread baseline (roughly 80% of the baseline loss).

## Run

```sh
MAKEFUN_INPUT_DIR=<cases> MAKEFUN_OUTPUT_DIR=<out> python3 main.py
```

Pure standard library, no network, deterministic.
