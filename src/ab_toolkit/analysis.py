"""Run the full analysis for each experiment and reach a decision with explicit rules."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import power as P
from . import stats as S
from .config import ALPHA

BASE_RATE, PLANNED_MDE, DAILY_VISITORS = 0.032, 0.10, 7_143

SPECS = {
    "checkout_redesign": {"title": "One-page checkout redesign",
                          "hypothesis": "A shorter, one-page checkout will raise the share of visitors who buy.",
                          "change": "Checkout reduced from three steps to one page."},
    "free_delivery_30": {"title": "Free delivery from £30 (was £40)",
                         "hypothesis": "A lower free-delivery threshold will raise conversion without cutting revenue.",
                         "change": "Free-delivery threshold lowered from £40 to £30."},
    "recommendations_widget": {"title": "'You may also like' widget",
                               "hypothesis": "Product recommendations on the basket page will raise conversion.",
                               "change": "Recommendation carousel added to the basket page."},
    "unit_price_display": {"title": "Show price per unit",
                           "hypothesis": "Showing price per unit on multipacks will raise conversion.",
                           "change": "Unit price shown under the main price."},
    "email_subject_line": {"title": "Personalised email subject line",
                           "hypothesis": "A personalised subject line will raise 30-day spend of loyalty members.",
                           "change": "Subject line includes the member's first name and last category viewed."},
}


def plan() -> dict:
    n = P.sample_size_proportion(BASE_RATE, PLANNED_MDE)
    return {"baseline_conversion": BASE_RATE, "mde_relative": PLANNED_MDE, "alpha": ALPHA, "power": 0.8,
            "n_per_group": n, "daily_visitors": DAILY_VISITORS,
            "duration_days": P.duration_days(n, DAILY_VISITORS)}


def _groups(df: pd.DataFrame):
    return df[df["group"] == "control"], df[df["group"] == "treatment"]


def decide(primary: S.Result, srm: dict, guardrails: list[dict], mde_abs: float | None = None) -> tuple[str, str]:
    """Decision rules, applied in order:
    1. SRM detected            -> INVESTIGATE: the split is broken, results cannot be trusted.
    2. A guardrail got worse   -> DO NOT SHIP.
    3. Primary significantly up   -> SHIP.
    4. Primary significantly down -> DO NOT SHIP.
    5. Not significant: if the whole CI is smaller than the effect we cared about -> NO MEANINGFUL EFFECT;
       otherwise INCONCLUSIVE (the test could not tell)."""
    if srm["srm_detected"]:
        return "INVESTIGATE", (f"Sample ratio mismatch: treatment got {100 * srm['observed_share_t']:.1f}% of users "
                               f"instead of 50% (p = {srm['p_value']:.1e}). Fix tracking and re-run; do not use this result.")
    bad = [g for g in guardrails if g["worse"]]
    if bad:
        return "DO NOT SHIP", f"Guardrail harmed: {', '.join(g['metric'] for g in bad)}."
    if primary.significant and primary.abs_diff > 0:
        return "SHIP", (f"{primary.metric} up {100 * primary.rel_diff:+.1f}% (95% CI {primary.ci_low:+.4g} to "
                        f"{primary.ci_high:+.4g}, p = {primary.p_value:.3g}); guardrails fine.")
    if primary.significant:
        return "DO NOT SHIP", f"{primary.metric} significantly worse ({100 * primary.rel_diff:+.1f}%)."
    if mde_abs is not None and max(abs(primary.ci_low), abs(primary.ci_high)) < mde_abs:
        return "NO MEANINGFUL EFFECT", ("Not significant, and the 95% CI rules out a lift as large as the one we planned "
                                        "for. A smaller lift cannot be excluded, but it would not justify the change on its own.")
    return "INCONCLUSIVE", (f"Not significant (p = {primary.p_value:.2f}); the 95% CI ({primary.ci_low:+.4g} to "
                            f"{primary.ci_high:+.4g}) still includes effects worth having. Do not ship on this evidence.")


def analyse_web(name: str, df: pd.DataFrame) -> dict:
    c, t = _groups(df)
    srm = S.srm_check(len(c), len(t))
    conv = S.two_proportion_ztest(c["converted"].sum(), len(c), t["converted"].sum(), len(t), "Conversion rate")
    bayes = S.bayes_proportions(c["converted"].sum(), len(c), t["converted"].sum(), len(t))
    rpv = S.bootstrap_diff(c["revenue"], t["revenue"], "Revenue per visitor (£)", n_boot=2000)
    cb, tb = c[c["converted"] == 1], t[t["converted"] == 1]
    aov = S.welch_ttest(cb["revenue"], tb["revenue"], "Average order value (£)")
    ret = S.two_proportion_ztest(cb["returned"].sum(), len(cb), tb["returned"].sum(), len(tb), "Return rate")
    guard = [{"metric": "Return rate", "result": ret.to_dict(), "worse": bool(ret.significant and ret.abs_diff > 0)}]
    # segments, with multiple-testing adjustment
    segs = []
    for (dev, vis), g in df.groupby(["device", "visitor_type"]):
        gc, gt = _groups(g)
        r = S.two_proportion_ztest(gc["converted"].sum(), len(gc), gt["converted"].sum(), len(gt), "Conversion rate")
        segs.append({"segment": f"{dev} / {vis}", **{k: r.to_dict()[k] for k in ("control", "treatment", "rel_diff", "ci_low", "ci_high", "p_value", "n_control", "n_treatment")}})
    pvals = [s["p_value"] for s in segs]
    for s, h, b in zip(segs, S.adjust_pvalues(pvals, "holm"), S.adjust_pvalues(pvals, "bh")):
        s["p_holm"], s["p_bh"] = h, b
    # daily cumulative view (what a dashboard would have shown)
    daily = (df.groupby(["date", "group"])["converted"].agg(["sum", "count"]).groupby(level="group").cumsum()
             .reset_index())
    daily["cum_rate"] = daily["sum"] / daily["count"]
    by_device = df.groupby(["device", "group"]).size().unstack()
    decision, reason = decide(conv, srm, guard, mde_abs=PLANNED_MDE * BASE_RATE)
    return {"name": name, **SPECS[name], "kind": "web", "srm": srm, "primary": conv.to_dict(), "bayes": bayes,
            "secondary": [rpv.to_dict(), aov.to_dict()], "guardrails": guard, "segments": segs,
            "daily": daily, "by_device": by_device, "decision": decision, "reason": reason,
            "users": len(df)}


def analyse_email(df: pd.DataFrame) -> dict:
    name = "email_subject_line"
    c, t = _groups(df)
    srm = S.srm_check(len(c), len(t))
    raw = S.welch_ttest(c["spend_30d"], t["spend_30d"], "30-day spend (£), unadjusted")
    adj, theta = S.cuped(df["spend_30d"], df["pre_period_spend"])
    df = df.assign(spend_cuped=adj)
    c2, t2 = _groups(df)
    cup = S.welch_ttest(c2["spend_cuped"], t2["spend_cuped"], "30-day spend (£), CUPED")
    opened = S.two_proportion_ztest(c["opened"].sum(), len(c), t["opened"].sum(), len(t), "Open rate")
    pre = S.welch_ttest(c["pre_period_spend"], t["pre_period_spend"], "Spend before the email (£)")
    var_red = 1 - df["spend_cuped"].var() / df["spend_30d"].var()
    decision, reason = decide(cup, srm, [], None)
    return {"name": name, **SPECS[name], "kind": "email", "srm": srm, "primary": cup.to_dict(), "raw": raw.to_dict(),
            "secondary": [opened.to_dict()], "pre_period_check": pre.to_dict(), "theta": theta,
            "variance_reduction": float(var_red),
            "ci_width_reduction": float(1 - (cup.ci_high - cup.ci_low) / (raw.ci_high - raw.ci_low)),
            "guardrails": [], "decision": decision, "reason": reason, "users": len(df), "frame": df}


def aa_validation(n_sims: int = 2000, n: int = 20_000, p: float = BASE_RATE, seed: int = 7) -> dict:
    """Run the z-test on thousands of simulated A/A tests (no real difference). About 5% should be
    'significant', and p-values should be spread evenly between 0 and 1."""
    rng = np.random.default_rng(seed)
    xs = rng.binomial(n, p, (n_sims, 2))
    pv = np.array([S.two_proportion_ztest(a, n, b, n).p_value for a, b in xs])
    return {"sims": n_sims, "false_positive_rate": float((pv < ALPHA).mean()), "p_values": pv}
