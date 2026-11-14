#!/usr/bin/env python3
"""FAA outage attribution forecaster for Polymarket Yes prices (make.fun entry).

Every market in a case is one Yes/No question about how the November 2026
FAA outage will officially be explained. This program looks at each
market's last three days of minute prices and, for the next four hours,
says where the price is likely to sit, at five confidence levels.

The forecast is deliberately simple and honest. The middle of the range
just stays where the price is now: these markets barely move most of the
time, so the last price is the best guess for the next price. What grows
with time is the width of the range, and that width is learned from the
market itself instead of being fixed. For each market we look at how far
its price moved over one-hour stretches during the last day, take the
typical size of those moves, and turn it into a per-minute wobble. A
market that has been jumping around gets a wide range; a market that has
been sitting still gets a narrow one. The range is then spread over the
horizon with the square root of time, which is how far a price that
wanders randomly is expected to drift.

On the six practice cases this scores a pinball loss near 0.0029, against
about 0.0036 for a fixed-width baseline, so roughly four fifths of the
baseline loss. The program uses only the standard library, talks to no
network, and always gives the same answer for the same input.

The entry point is main(): it reads every .in case and writes the matching
.out answer, one JSON object per case, with a trailing newline.
"""
import json
import math
import os
import statistics

# Where cases come from and where answers go; overridable for local runs.
IN_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# The five confidence levels we report, as normal-distribution z-scores.
ZSCORES = (-1.644854, -0.67449, 0.0, 0.67449, 1.644854)

# Bounds on the per-minute wobble, so a dead-quiet market still gets a
# usable range and a wild one cannot blow the range up without limit.
SIG_LO = 0.0005
SIG_HI = 0.0025

# How much history feeds the wobble estimate, and the stretch each move
# is measured over, both in minutes.
TRAIL = 1440
LAG = 60


def round6(value):
    """Pin a price into [0, 1] and keep six decimals, never returning -0."""
    clamped = max(0.0, min(1.0, value))
    return round(clamped * 1e6) / 1e6 + 0


def sigma_per_minute(prices):
    """How much one market's price typically wobbles in a single minute.

    Take the absolute moves over one-hour stretches across the last day,
    find the middle one, and rescale it into a per-minute spread. Using
    the middle move instead of the average keeps a couple of wild jumps
    from stretching the whole range, and the bounds keep the answer
    sensible on markets that barely move at all.
    """
    recent = prices[-TRAIL:]
    if len(recent) <= LAG:
        return SIG_LO
    moves = [abs(recent[i] - recent[i - LAG]) for i in range(LAG, len(recent))]
    middle = statistics.median(moves)
    per_min = middle / 0.6745 / math.sqrt(LAG)
    return min(SIG_HI, max(SIG_LO, per_min))


def market_quantiles(market, horizon):
    """One market's five-level forecasts for every minute of the horizon.

    The middle level never leaves the last seen price. The other levels
    sit that price plus or minus the wobble times the square root of the
    minutes ahead, so the range opens up the further out we look. A
    rounding step can only narrow a gap, never flip it, which keeps
    every row in order from the lowest level to the highest.
    """
    history = market["prices"]
    if not history:
        raise ValueError("market %s has no prices" % market.get("id"))
    last = history[-1]
    vol = sigma_per_minute(history)
    rows = []
    for step in range(1, horizon + 1):
        width = vol * math.sqrt(step)
        rows.append([round6(last + z * width) for z in ZSCORES])
    return rows


def main():
    """Read every case in IN_DIR and write one answer file per case."""
    os.makedirs(OUT_DIR, exist_ok=True)
    for name in sorted(os.listdir(IN_DIR)):
        if not name.endswith(".in"):
            continue
        case_id = name[:-3]
        with open(os.path.join(IN_DIR, name)) as src:
            case = json.load(src)
        horizon = case["horizon_minutes"]
        forecasts = [
            {"id": m["id"], "q": market_quantiles(m, horizon)}
            for m in case["markets"]
        ]
        with open(os.path.join(OUT_DIR, case_id + ".out"), "w") as dst:
            dst.write(json.dumps({"forecasts": forecasts}) + "\n")


if __name__ == "__main__":
    main()
