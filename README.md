# polymarket-faa-attribution-02

Forecast, minute by minute and 4 hours ahead, the Yes price of every
Polymarket market for how the 13 Nov 2026 FAA outage gets officially
attributed.

## Model

Persistence center + a per-market spread that adapts to that market's own
recent movement. Each market's per-minute sigma is estimated robustly
from the median absolute 60-minute price change over the trailing 24h
(MAD -> stdev), floored at 0.0005 and capped at 0.0025. Quantiles:
`q_tau(h) = clamp(x + z_tau * sigma * sqrt(h), 0, 1)`.

Backtested on the 6 NVIDIA-CEO practice cases with realized Polymarket
futures: pinball 0.00293 vs the house baseline's 0.00364 (~80% of house).
Mean reversion hurts; the adaptive sigma is what wins.

## Run

```sh
python3 main.py   # reads /input/*.in, writes /output/*.out
```

Pure stdlib, no network, deterministic. MIT licensed.
