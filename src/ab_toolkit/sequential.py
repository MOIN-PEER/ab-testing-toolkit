"""Why you must not 'peek': simulated A/A tests, and a group-sequential fix.

If you check a test every day and stop as soon as p < 0.05, the chance of a false 'win' rises far
above 5%. A group-sequential design with O'Brien-Fleming-style boundaries allows planned looks while
keeping the overall false-positive rate at 5%: early looks need much stronger evidence.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .config import ALPHA, SEED


def _cumulative_z(rng, n_sims: int, looks: int, n_per_look: int, p: float, lift: float) -> np.ndarray:
    """z statistic at each look for many simulated experiments (shape: sims x looks)."""
    c = rng.binomial(n_per_look, p, (n_sims, looks)).cumsum(axis=1)
    t = rng.binomial(n_per_look, p * (1 + lift), (n_sims, looks)).cumsum(axis=1)
    n = n_per_look * np.arange(1, looks + 1)
    pc, pt = c / n, t / n
    pool = (c + t) / (2 * n)
    se = np.sqrt(pool * (1 - pool) * 2 / n)
    return np.where(se > 0, (pt - pc) / np.where(se > 0, se, 1), 0.0)


def obf_boundaries(looks: int, alpha: float = ALPHA, sims: int = 200_000, seed: int = SEED) -> np.ndarray:
    """O'Brien-Fleming shape z_k = C * sqrt(K / k), with C calibrated by simulation of correlated
    Brownian increments so that P(cross any boundary | no effect) = alpha (two-sided)."""
    rng = np.random.default_rng(seed)
    inc = rng.standard_normal((sims, looks))
    z = inc.cumsum(axis=1) / np.sqrt(np.arange(1, looks + 1))
    shape = np.sqrt(looks / np.arange(1, looks + 1))
    lo, hi = 1.5, 4.0
    for _ in range(50):
        c = (lo + hi) / 2
        rate = (np.abs(z) >= c * shape).any(axis=1).mean()
        lo, hi = (c, hi) if rate > alpha else (lo, c)
    return hi * shape


def peeking_simulation(looks: int = 14, n_per_look: int = 3_500, p: float = 0.032, lift: float = 0.0,
                       sims: int = 4_000, seed: int = SEED) -> dict:
    """Compare three policies on the same simulated experiments:
    peek daily at p < 0.05, analyse once at the end, and group-sequential (OBF) boundaries."""
    rng = np.random.default_rng(seed)
    z = _cumulative_z(rng, sims, looks, n_per_look, p, lift)
    crit = norm.ppf(1 - ALPHA / 2)
    bounds = obf_boundaries(looks)
    peek_hit = np.abs(z) >= crit
    obf_hit = np.abs(z) >= bounds
    first_obf = np.where(obf_hit.any(axis=1), obf_hit.argmax(axis=1) + 1, looks)
    return {"looks": looks, "n_per_look_per_group": n_per_look, "lift": lift, "sims": sims,
            "peek_every_day_rate": float(peek_hit.any(axis=1).mean()),
            "single_final_look_rate": float(peek_hit[:, -1].mean()),
            "group_sequential_rate": float(obf_hit.any(axis=1).mean()),
            "group_sequential_avg_stop_day": float(first_obf.mean()),
            "peek_rate_by_day": peek_hit.cumsum(axis=1).clip(0, 1).mean(axis=0).tolist(),
            "obf_boundaries": bounds.tolist()}
