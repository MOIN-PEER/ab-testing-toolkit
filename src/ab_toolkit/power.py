"""Planning: sample size, minimum detectable effect and test duration."""

from __future__ import annotations

import math

from scipy.stats import norm

from .config import ALPHA, POWER


def _z(alpha: float, power: float, two_sided: bool = True) -> tuple[float, float]:
    za = norm.ppf(1 - alpha / 2) if two_sided else norm.ppf(1 - alpha)
    return za, norm.ppf(power)


def sample_size_proportion(p_base: float, mde_rel: float, alpha: float = ALPHA, power: float = POWER,
                           ratio: float = 1.0) -> int:
    """Visitors needed in the CONTROL group to detect a relative lift `mde_rel` on a conversion rate.

    Uses the standard normal approximation with unpooled variances.
    ratio = treatment size / control size.
    """
    p1, p2 = p_base, p_base * (1 + mde_rel)
    if not (0 < p1 < 1 and 0 < p2 < 1):
        raise ValueError("rates must be between 0 and 1")
    za, zb = _z(alpha, power)
    var = p1 * (1 - p1) + p2 * (1 - p2) / ratio
    return math.ceil((za + zb) ** 2 * var / (p2 - p1) ** 2)


def sample_size_mean(sd: float, mde_abs: float, alpha: float = ALPHA, power: float = POWER, ratio: float = 1.0) -> int:
    """Units needed in the CONTROL group to detect an absolute change `mde_abs` in a mean."""
    za, zb = _z(alpha, power)
    return math.ceil((za + zb) ** 2 * sd ** 2 * (1 + 1 / ratio) / mde_abs ** 2)


def mde_proportion(p_base: float, n_per_group: int, alpha: float = ALPHA, power: float = POWER) -> float:
    """Smallest relative lift detectable with n visitors per group (solved numerically)."""
    lo, hi = 1e-5, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if p_base * (1 + mid) >= 1:
            hi = mid
            continue
        if sample_size_proportion(p_base, mid, alpha, power) > n_per_group:
            lo = mid
        else:
            hi = mid
    return hi


def duration_days(n_per_group: int, daily_visitors: float, share_in_test: float = 1.0, groups: int = 2) -> int:
    """Days needed, rounded UP to whole weeks so every weekday is covered equally."""
    days = math.ceil(n_per_group * groups / (daily_visitors * share_in_test))
    return max(7, math.ceil(days / 7) * 7)


def achieved_power(p_base: float, mde_rel: float, n_per_group: int, alpha: float = ALPHA) -> float:
    p1, p2 = p_base, p_base * (1 + mde_rel)
    se = math.sqrt(p1 * (1 - p1) / n_per_group + p2 * (1 - p2) / n_per_group)
    za = norm.ppf(1 - alpha / 2)
    return float(norm.cdf(abs(p2 - p1) / se - za))
