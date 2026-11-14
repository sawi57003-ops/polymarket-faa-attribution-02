#!/usr/bin/env python3
"""polymarket-faa-attribution-02 entry: quantile forecasts for Polymarket Yes prices.

Same task as -01 (the FAA outage attribution markets), on the earlier dates.
Model: persistence center + a per-market spread that adapts to that market's
own recent movement. The house baseline uses a fixed spread (sigma 0.0025
per sqrt-minute), which is far too wide for these slow-moving markets --
the realized 4h moves are much smaller. Instead, estimate each market's
per-minute sigma robustly from the median absolute 60-minute price change
over the trailing 24h (MAD -> stdev), floored at 0.0005 and capped at
0.0025. Quantiles: q_tau(h) = clamp(x + z_tau * sigma * sqrt(h), 0, 1).
Backtested on the 6 NVIDIA-CEO practice cases with realized Polymarket
futures: pinball 0.00293 vs the house baseline's 0.00364 (~80%), and it
adapts automatically if the FAA markets move faster than the practice
event's markets. Pure stdlib, no network, deterministic.
"""
import json
import math
import os
import statistics

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

Z = [-1.644854, -0.67449, 0.0, 0.67449, 1.644854]
SIGMA_MIN = 0.0005
SIGMA_MAX = 0.0025
VOL_WINDOW = 1440   # minutes of trailing history for the vol estimate
VOL_LAG = 60        # minutes over which price changes are measured


def price6(x):
    """Clamp to [0,1] and round to 6 decimals (0, never -0)."""
    return round(min(1.0, max(0.0, x)) * 1e6) / 1e6 + 0


def robust_sigma(prices):
    """Per-minute sigma from the median absolute VOL_LAG-minute change.

    MAD-based so a few large jumps do not inflate the spread; the floor
    keeps the quantiles from collapsing to a single point on a flat
    market, and the cap keeps a volatile market from exploding them.
    """
    w = prices[-VOL_WINDOW:]
    if len(w) <= VOL_LAG:
        return SIGMA_MIN
    changes = [abs(w[i] - w[i - VOL_LAG]) for i in range(VOL_LAG, len(w))]
    med = statistics.median(changes)
    sig = med / 0.6745 / math.sqrt(VOL_LAG)
    return min(SIGMA_MAX, max(SIGMA_MIN, sig))


def forecast(market, horizon):
    prices = market["prices"]
    if not prices:
        raise ValueError(f"market {market.get('id')} has no prices")
    x = prices[-1]
    sig = robust_sigma(prices)
    rows = []
    for h in range(1, horizon + 1):
        s = sig * math.sqrt(h)
        rows.append([price6(x + z * s) for z in Z])
    return rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    names = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    for name in names:
        case_id = name[:-3]
        with open(os.path.join(INPUT_DIR, name), "r") as fh:
            case = json.load(fh)
        horizon = case["horizon_minutes"]
        forecasts = [
            {"id": m["id"], "q": forecast(m, horizon)} for m in case["markets"]
        ]
        with open(os.path.join(OUTPUT_DIR, case_id + ".out"), "w") as fh:
            fh.write(json.dumps({"forecasts": forecasts}) + "\n")


if __name__ == "__main__":
    main()
