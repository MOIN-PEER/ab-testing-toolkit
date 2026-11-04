"""Synthetic experiment logs for "Lagan Living", a fictional online homeware retailer.

Every experiment has a KNOWN true effect, so the toolkit's conclusions can be checked:

  E1 checkout_redesign      +10% relative conversion, no harm to returns          -> should ship
  E2 free_delivery_30       +6% conversion but -5% basket size                     -> revenue effect unclear
  E3 recommendations_widget no true effect                                          -> should find nothing
  E4 unit_price_display     +3% conversion, BUT a bot-filter bug drops treatment users (SRM) -> do not trust
  E5 email_subject_line     +£0.60 on 30-day spend (mean ~£18); pre-period spend available -> CUPED helps

All data is synthetic. No real customers or companies are represented.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DATA, SEED

DEVICES = np.array(["mobile", "desktop"])
VISITOR = np.array(["new", "returning"])


def _web_experiment(rng, name, n, days, base_cr, lift, aov_mean, aov_change=0.0, return_rate=0.08,
                    return_change=0.0, share_t=0.5, drop_t=0.0, start="2025-09-01"):
    group = np.where(rng.random(n) < share_t, "treatment", "control")
    device = rng.choice(DEVICES, n, p=[0.64, 0.36])
    visitor = rng.choice(VISITOR, n, p=[0.58, 0.42])
    day = rng.integers(0, days, n)
    # baseline differences: desktop and returning visitors convert more
    cr = base_cr * np.where(device == "desktop", 1.35, 0.80) * np.where(visitor == "returning", 1.45, 0.68)
    cr = cr * np.where(pd.Series(day % 7).isin([5, 6]).to_numpy(), 1.08, 1.0)
    t = group == "treatment"
    cr = np.where(t, cr * (1 + lift), cr)
    converted = rng.random(n) < np.clip(cr, 0, 0.95)
    sigma = 0.75
    mu = np.log(aov_mean) - sigma ** 2 / 2
    order_value = np.where(converted, rng.lognormal(mu, sigma, n) * np.where(t, 1 + aov_change, 1.0), 0.0)
    returned = converted & (rng.random(n) < np.where(t, return_rate * (1 + return_change), return_rate))
    df = pd.DataFrame({"experiment": name, "user_id": [f"{name[:3].upper()}{i:06d}" for i in range(n)],
                       "date": pd.Timestamp(start) + pd.to_timedelta(day, "D"), "group": group,
                       "device": device, "visitor_type": visitor, "converted": converted.astype(int),
                       "revenue": np.round(order_value, 2), "returned": returned.astype(int)})
    if drop_t:  # a tracking bug silently loses some treatment visitors (mostly non-buyers on mobile)
        lost = t & (device == "mobile") & ~converted & (rng.random(n) < drop_t)
        df = df[~lost]
    return df.reset_index(drop=True)


def _email_experiment(rng, n=40_000, effect=0.60):
    group = np.where(rng.random(n) < 0.5, "treatment", "control")
    loyalty = rng.gamma(1.4, 1.0, n)                         # how engaged each member is
    pre = rng.gamma(1.6, 11.0 * loyalty / 1.4, n)           # spend in the 30 days BEFORE the email
    expected = 0.7 * pre + 6.0 * loyalty + np.where(group == "treatment", effect, 0.0)
    spend = np.maximum(0, expected + rng.normal(0, 16.0, n))
    opened = rng.random(n) < np.where(group == "treatment", 0.29, 0.24)
    return pd.DataFrame({"experiment": "email_subject_line", "user_id": [f"EML{i:06d}" for i in range(n)],
                         "group": group, "pre_period_spend": np.round(pre, 2), "opened": opened.astype(int),
                         "spend_30d": np.round(spend, 2)})


def generate(seed: int = SEED) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    out = {
        "checkout_redesign": _web_experiment(rng, "checkout_redesign", 100_000, 14, 0.032, 0.10, 62.0),
        "free_delivery_30": _web_experiment(rng, "free_delivery_30", 100_000, 14, 0.032, 0.06, 62.0, aov_change=-0.05),
        "recommendations_widget": _web_experiment(rng, "recommendations_widget", 100_000, 14, 0.032, 0.0, 62.0),
        "unit_price_display": _web_experiment(rng, "unit_price_display", 100_000, 14, 0.032, 0.03, 62.0, drop_t=0.06),
        "email_subject_line": _email_experiment(rng),
    }
    return out


def write(seed: int = SEED) -> dict[str, pd.DataFrame]:
    DATA.mkdir(parents=True, exist_ok=True)
    data = generate(seed)
    for k, v in data.items():
        v.to_csv(DATA / f"{k}.csv", index=False)
    return data


def load() -> dict[str, pd.DataFrame]:
    names = ["checkout_redesign", "free_delivery_30", "recommendations_widget", "unit_price_display", "email_subject_line"]
    if not all((DATA / f"{n}.csv").exists() for n in names):
        return write()
    out = {n: pd.read_csv(DATA / f"{n}.csv") for n in names}
    for n in names[:4]:
        out[n]["date"] = pd.to_datetime(out[n]["date"])
    return out
