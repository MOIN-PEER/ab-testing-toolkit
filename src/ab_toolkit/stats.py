"""Analysis: frequentist tests, bootstrap, Bayesian comparison, CUPED, SRM and multiple testing."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy import stats

from .config import ALPHA, SRM_ALPHA


@dataclass
class Result:
    metric: str
    control: float
    treatment: float
    abs_diff: float
    rel_diff: float
    ci_low: float          # CI for the absolute difference
    ci_high: float
    p_value: float
    method: str
    n_control: int
    n_treatment: int

    @property
    def significant(self) -> bool:
        return self.p_value < ALPHA

    def to_dict(self) -> dict:
        d = asdict(self)
        d["significant"] = self.significant
        return d


def two_proportion_ztest(x_c: int, n_c: int, x_t: int, n_t: int, metric: str = "conversion",
                         alpha: float = ALPHA) -> Result:
    """Pooled z-test for the p-value; unpooled standard error for the confidence interval."""
    p_c, p_t = x_c / n_c, x_t / n_t
    p_pool = (x_c + x_t) / (n_c + n_t)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z = (p_t - p_c) / se_pool
    p = 2 * stats.norm.sf(abs(z))
    se = np.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    zc = stats.norm.ppf(1 - alpha / 2)
    d = p_t - p_c
    return Result(metric, p_c, p_t, d, d / p_c, d - zc * se, d + zc * se, float(p), "two-proportion z-test", n_c, n_t)


def welch_ttest(c: np.ndarray, t: np.ndarray, metric: str = "mean", alpha: float = ALPHA) -> Result:
    c, t = np.asarray(c, float), np.asarray(t, float)
    res = stats.ttest_ind(t, c, equal_var=False)
    d = t.mean() - c.mean()
    v_c, v_t = c.var(ddof=1) / len(c), t.var(ddof=1) / len(t)
    se = np.sqrt(v_c + v_t)
    df = (v_c + v_t) ** 2 / (v_c ** 2 / (len(c) - 1) + v_t ** 2 / (len(t) - 1))
    q = stats.t.ppf(1 - alpha / 2, df)
    return Result(metric, c.mean(), t.mean(), d, d / c.mean(), d - q * se, d + q * se, float(res.pvalue),
                  "Welch t-test", len(c), len(t))


def bootstrap_diff(c: np.ndarray, t: np.ndarray, metric: str = "mean", n_boot: int = 2000, seed: int = 0,
                   alpha: float = ALPHA) -> Result:
    """Percentile bootstrap for the difference in means; robust for skewed metrics like revenue."""
    rng = np.random.default_rng(seed)
    c, t = np.asarray(c, float), np.asarray(t, float)
    bc = rng.choice(c, (n_boot, len(c))).mean(axis=1) if len(c) < 20000 else _fast_boot(rng, c, n_boot)
    bt = rng.choice(t, (n_boot, len(t))).mean(axis=1) if len(t) < 20000 else _fast_boot(rng, t, n_boot)
    diffs = bt - bc
    d = t.mean() - c.mean()
    lo, hi = np.quantile(diffs, [alpha / 2, 1 - alpha / 2])
    p = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
    return Result(metric, c.mean(), t.mean(), d, d / c.mean(), float(lo), float(hi), float(max(p, 1 / n_boot)),
                  "bootstrap (percentile)", len(c), len(t))


def _fast_boot(rng, x: np.ndarray, n_boot: int) -> np.ndarray:
    """Poisson bootstrap: each unit gets a Poisson(1) weight. Memory-friendly for large samples."""
    out = np.empty(n_boot)
    for b in range(n_boot):
        w = rng.poisson(1.0, len(x))
        out[b] = (w * x).sum() / max(w.sum(), 1)
    return out


def bayes_proportions(x_c: int, n_c: int, x_t: int, n_t: int, draws: int = 200_000, seed: int = 0,
                      prior: tuple[float, float] = (1, 1)) -> dict:
    """Beta-Binomial model. Returns P(treatment better), expected loss of shipping each arm and a credible interval."""
    rng = np.random.default_rng(seed)
    a, b = prior
    pc = rng.beta(a + x_c, b + n_c - x_c, draws)
    pt = rng.beta(a + x_t, b + n_t - x_t, draws)
    lift = pt / pc - 1
    return {"p_treatment_better": float((pt > pc).mean()),
            "expected_loss_ship_treatment": float(np.maximum(pc - pt, 0).mean()),
            "expected_loss_keep_control": float(np.maximum(pt - pc, 0).mean()),
            "rel_lift_median": float(np.median(lift)),
            "rel_lift_95ci": [float(np.quantile(lift, 0.025)), float(np.quantile(lift, 0.975))]}


def cuped(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, float]:
    """CUPED: subtract the part of the metric explained by a pre-experiment covariate.

    theta is estimated on the pooled data (both groups), which keeps the estimate unbiased because
    the covariate was measured before randomisation.
    """
    y, x = np.asarray(y, float), np.asarray(x, float)
    theta = np.cov(y, x, ddof=1)[0, 1] / np.var(x, ddof=1)
    return y - theta * (x - x.mean()), float(theta)


def srm_check(n_c: int, n_t: int, expected_share_t: float = 0.5) -> dict:
    """Sample ratio mismatch: is the split between groups what we designed? A failure means the
    randomisation or tracking is broken and the result should not be trusted."""
    total = n_c + n_t
    exp = [total * (1 - expected_share_t), total * expected_share_t]
    chi2, p = stats.chisquare([n_c, n_t], exp)
    return {"n_control": n_c, "n_treatment": n_t, "observed_share_t": n_t / total,
            "expected_share_t": expected_share_t, "chi2": float(chi2), "p_value": float(p),
            "srm_detected": bool(p < SRM_ALPHA)}


def adjust_pvalues(p: list[float], method: str = "holm") -> list[float]:
    """Bonferroni, Holm (family-wise error) or Benjamini-Hochberg (false discovery rate)."""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    if method == "bonferroni":
        return list(np.minimum(p * m, 1))
    adj = np.empty(m)
    if method == "holm":
        running = 0.0
        for rank, i in enumerate(order):
            running = max(running, (m - rank) * p[i])
            adj[i] = min(running, 1)
        return list(adj)
    if method == "bh":
        running = 1.0
        for rank in range(m - 1, -1, -1):
            i = order[rank]
            running = min(running, p[i] * m / (rank + 1))
            adj[i] = running
        return list(adj)
    raise ValueError(method)
