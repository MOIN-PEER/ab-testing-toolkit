"""Figures, per-experiment decision reports, result tables and a summary."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import power as P  # noqa: E402
from .analysis import BASE_RATE, PLANNED_MDE  # noqa: E402
from .config import FIGURES, REPORTS, RESULTS  # noqa: E402

C, T, ACC, RED, GREY, AMB = "#8A96A3", "#2E6F9E", "#2E6F9E", "#C0392B", "#9AA5B1", "#D68910"
DEC_COL = {"SHIP": "#1E8449", "DO NOT SHIP": RED, "INVESTIGATE": AMB, "INCONCLUSIVE": "#7F8C8D", "NO MEANINGFUL EFFECT": "#5D6D7E"}
plt.rcParams.update({"figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left"})


def _save(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def figures(exps: list[dict], peek0: dict, peek1: dict, aa: dict) -> None:
    web = [e for e in exps if e["kind"] == "web"]
    # 01 power: sample size vs MDE
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    mdes = np.linspace(0.03, 0.30, 60)
    for p, col in ((0.02, GREY), (0.032, ACC), (0.05, "#5DADE2")):
        ax.plot(mdes * 100, [P.sample_size_proportion(p, m) / 1000 for m in mdes], color=col, lw=2,
                label=f"baseline {p:.1%}")
    n = P.sample_size_proportion(BASE_RATE, PLANNED_MDE)
    ax.scatter([PLANNED_MDE * 100], [n / 1000], color=RED, zorder=3)
    ax.annotate(f"plan: 10% lift on 3.2%\n= {n:,} per group, 14 days", (10, n / 1000), xytext=(13, n / 1000 + 60),
                fontsize=9, arrowprops=dict(arrowstyle="-", color="#666"))
    ax.set_yscale("log"); ax.set_xlabel("smallest lift we want to detect (%)"); ax.set_ylabel("visitors per group (thousands, log)")
    ax.set_title("How many visitors a test needs"); ax.legend(frameon=False)
    _save(fig, "01_sample_size.png")

    # 02 forest plot of primary results
    fig, ax = plt.subplots(figsize=(9, 3.8))
    rows = list(reversed(exps))
    for i, e in enumerate(rows):
        pr = e["primary"]
        base = pr["control"]
        lo, hi, mid = 100 * pr["ci_low"] / base, 100 * pr["ci_high"] / base, 100 * pr["rel_diff"]
        col = DEC_COL[e["decision"]]
        ax.plot([lo, hi], [i, i], color=col, lw=3, solid_capstyle="round")
        ax.scatter([mid], [i], color=col, s=50, zorder=3)
        ax.text(hi + 1, i, e["decision"], va="center", fontsize=8.5, color=col, weight="bold")
    ax.axvline(0, color="#333", lw=0.8)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([e["title"] for e in rows], fontsize=9)
    ax.set_xlabel("relative change in the primary metric, % (95% CI)")
    ax.set_title("Five experiments, five different answers")
    ax.set_xlim(None, ax.get_xlim()[1] + 9)
    _save(fig, "02_experiment_results.png")

    # 03 E1 cumulative conversion by day
    e1 = next(e for e in web if e["name"] == "checkout_redesign")
    d = e1["daily"]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for g, col in (("control", C), ("treatment", T)):
        s = d[d["group"] == g]
        ax.plot(s["date"], 100 * s["cum_rate"], marker="o", ms=3, color=col, label=g)
    ax.set_ylabel("cumulative conversion (%)"); ax.set_title("Checkout redesign: cumulative conversion by day")
    ax.legend(frameon=False); ax.tick_params(axis="x", rotation=30, labelsize=8)
    _save(fig, "03_checkout_cumulative.png")

    # 04 SRM: users by device and group for E4 vs E1
    e4 = next(e for e in web if e["name"] == "unit_price_display")
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for ax, e in zip(axs, (e1, e4)):
        bd = e["by_device"]
        x = np.arange(len(bd))
        share = bd["treatment"] / bd.sum(axis=1)
        ax.bar(x, 100 * share, color=[AMB if (e["srm"]["srm_detected"] and v < 0.495) else T for v in share])
        ax.axhline(50, color="#333", ls="--", lw=0.8)
        for i, v in enumerate(share):
            ax.text(i, 100 * v + 0.15, f"{100 * v:.1f}%", ha="center", fontsize=9)
        ax.set_xticks(x); ax.set_xticklabels(bd.index); ax.set_ylim(46, 51.5)
        ax.set_title(("Healthy split: " if not e["srm"]["srm_detected"] else "Sample ratio mismatch: ") + e["title"], fontsize=10.5)
    axs[0].set_ylabel("share of users in treatment (%)")
    _save(fig, "04_srm_check.png")

    # 05 CUPED
    em = next(e for e in exps if e["kind"] == "email")
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
    f = em["frame"].sample(4000, random_state=1)
    axs[0].scatter(f["pre_period_spend"], f["spend_30d"], s=4, alpha=0.35, color=ACC)
    axs[0].set_xlabel("spend in the 30 days BEFORE the email (£)"); axs[0].set_ylabel("spend in the 30 days after (£)")
    axs[0].set_title("Past spend predicts future spend")
    for i, (r, lab) in enumerate(((em["raw"], "Unadjusted"), (em["primary"], "CUPED-adjusted"))):
        axs[1].plot([r["ci_low"], r["ci_high"]], [i, i], lw=6, color=GREY if i == 0 else ACC, solid_capstyle="round")
        axs[1].scatter([r["abs_diff"]], [i], color="#111", zorder=3)
        axs[1].text(r["ci_high"] + 0.05, i, f"£{r['abs_diff']:.2f}  (±£{(r['ci_high'] - r['ci_low']) / 2:.2f})", va="center", fontsize=9)
    axs[1].axvline(0.60, color=RED, ls="--", lw=1); axs[1].text(0.61, 1.35, "true effect £0.60", color=RED, fontsize=8.5)
    axs[1].axvline(0, color="#333", lw=0.8)
    axs[1].set_yticks([0, 1]); axs[1].set_yticklabels(["Unadjusted", "CUPED"]); axs[1].set_ylim(-0.6, 1.6)
    axs[1].set_xlabel("effect on 30-day spend per member (£, 95% CI)"); axs[1].set_title("CUPED: closer to the truth, narrower interval")
    axs[1].set_xlim(-0.2, 2.3)
    _save(fig, "05_cuped.png")

    # 06 peeking
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
    days = np.arange(1, peek0["looks"] + 1)
    axs[0].plot(days, 100 * np.array(peek0["peek_rate_by_day"]), marker="o", color=RED, label="peek every day, stop at p < 0.05")
    axs[0].axhline(5, color="#333", ls="--", lw=0.8); axs[0].text(8, 6.0, "the 5% you think you have", fontsize=8.5)
    axs[0].set_xlabel("day of the test"); axs[0].set_ylabel("false 'wins' so far (%)")
    axs[0].set_title(f"Peeking: {100 * peek0['peek_every_day_rate']:.0f}% false wins in A/A tests"); axs[0].legend(frameon=False, fontsize=8)
    axs[1].plot(days, peek0["obf_boundaries"], marker="o", color=ACC, label="group-sequential boundary")
    axs[1].axhline(1.96, color=RED, ls="--", lw=1, label="naive 1.96 every day")
    axs[1].set_xlabel("look (day)"); axs[1].set_ylabel("|z| needed to stop"); axs[1].set_ylim(0, 8.5)
    axs[1].set_title("The fix: demand more evidence early"); axs[1].legend(frameon=False, fontsize=8)
    _save(fig, "06_peeking.png")

    # 07 segments with multiple-testing adjustment (null experiment)
    e3 = next(e for e in web if e["name"] == "recommendations_widget")
    sg = pd.DataFrame(e3["segments"])
    fig, ax = plt.subplots(figsize=(8, 3.4))
    y = np.arange(len(sg))
    ax.barh(y + 0.2, sg["p_value"], 0.4, color=AMB, label="raw p-value")
    ax.barh(y - 0.2, sg["p_holm"], 0.4, color=ACC, label="Holm-adjusted")
    ax.axvline(0.05, color=RED, ls="--", lw=1); ax.text(0.06, -0.75, "0.05", color=RED, fontsize=8.5)
    ax.set_yticks(y); ax.set_yticklabels(sg["segment"]); ax.set_xlabel("p-value")
    ax.set_title("Widget test (no real effect): one segment looks 'significant' until adjusted"); ax.legend(frameon=False, fontsize=8)
    _save(fig, "07_segments_multiple_testing.png")

    # 08 Bayesian posterior lift
    fig, ax = plt.subplots(figsize=(8, 3.6))
    rng = np.random.default_rng(0)
    for e, col in ((e1, ACC), (e3, GREY)):
        pr = e["primary"]
        nc, nt = pr["n_control"], pr["n_treatment"]
        xc, xt = round(pr["control"] * nc), round(pr["treatment"] * nt)
        lift = 100 * (rng.beta(1 + xt, 1 + nt - xt, 100000) / rng.beta(1 + xc, 1 + nc - xc, 100000) - 1)
        ax.hist(lift, bins=120, density=True, alpha=0.55, color=col,
                label=f"{e['title']}: P(better) = {100 * e['bayes']['p_treatment_better']:.1f}%")
    ax.axvline(0, color="#333", lw=0.8); ax.set_xlabel("relative lift in conversion (%)"); ax.set_yticks([])
    ax.set_title("Bayesian view: how likely is the new version better?"); ax.legend(frameon=False, fontsize=8.5)
    _save(fig, "08_bayesian_lift.png")

    # 09 A/A validation
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.hist(aa["p_values"], bins=20, color=ACC, edgecolor="white")
    ax.axhline(aa["sims"] / 20, color=RED, ls="--", lw=1)
    ax.set_xlabel("p-value"); ax.set_ylabel("number of A/A tests")
    ax.set_title(f"Testing the test: {aa['sims']:,} A/A tests, {100 * aa['false_positive_rate']:.1f}% false positives")
    _save(fig, "09_aa_validation.png")


def _fmt(v, pct=False):
    return f"{100 * v:.2f}%" if pct else (f"£{v:,.2f}" if abs(v) >= 1 else f"{v:.4f}")


def write_reports(exps: list[dict], plan: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    for e in exps:
        pr = e["primary"]
        pct = "rate" in pr["metric"].lower()
        L = [f"# Experiment report: {e['title']}", "", "*Synthetic data (fictional retailer Lagan Living).*", "",
             f"**Decision: {e['decision']}**. {e['reason']}", "", "## Design",
             f"* Change: {e['change']}", f"* Hypothesis: {e['hypothesis']}", f"* Users analysed: {e['users']:,}"]
        if e["kind"] == "web":
            L.append(f"* Planned before launch: detect a {plan['mde_relative']:.0%} relative lift on a {plan['baseline_conversion']:.1%} "
                     f"conversion rate with 80% power at alpha 0.05, so {plan['n_per_group']:,} visitors per group over "
                     f"{plan['duration_days']} days.")
        s = e["srm"]
        L += ["", "## Health check: sample ratio", f"* Control {s['n_control']:,} / treatment {s['n_treatment']:,} "
              f"({100 * s['observed_share_t']:.2f}% treatment, expected 50%), chi-square p = {s['p_value']:.3g}: "
              f"{'**MISMATCH, do not trust the results below**' if s['srm_detected'] else 'OK'}."]
        L += ["", "## Results", "", "| Metric | Control | Treatment | Change | 95% CI (absolute) | p-value | Method |", "|---|---|---|---|---|---|---|"]
        rows = [pr] + ([e["raw"]] if e["kind"] == "email" else []) + e["secondary"] + [g["result"] for g in e["guardrails"]]
        for r in rows:
            p2 = "rate" in r["metric"].lower()
            L.append(f"| {r['metric']} | {_fmt(r['control'], p2)} | {_fmt(r['treatment'], p2)} | {100 * r['rel_diff']:+.1f}% | "
                     f"{r['ci_low']:+.4g} to {r['ci_high']:+.4g} | {r['p_value']:.3g} | {r['method']} |")
        if e["kind"] == "web":
            b = e["bayes"]
            L += ["", f"Bayesian check (Beta(1,1) prior): P(treatment better) = {100 * b['p_treatment_better']:.1f}%, "
                  f"median lift {100 * b['rel_lift_median']:+.1f}% (95% credible interval {100 * b['rel_lift_95ci'][0]:+.1f}% "
                  f"to {100 * b['rel_lift_95ci'][1]:+.1f}%).",
                  "", "## Segments (exploratory, adjusted for 4 comparisons)", "",
                  "| Segment | Change | p-value | Holm-adjusted | BH-adjusted |", "|---|---|---|---|---|"]
            for sg in e["segments"]:
                L.append(f"| {sg['segment']} | {100 * sg['rel_diff']:+.1f}% | {sg['p_value']:.3f} | {sg['p_holm']:.3f} | {sg['p_bh']:.3f} |")
        else:
            L += ["", f"CUPED used each member's spend in the 30 days before the email (theta = {e['theta']:.3f}). "
                  f"It removed {100 * e['variance_reduction']:.0f}% of the variance and made the confidence interval "
                  f"{100 * e['ci_width_reduction']:.0f}% narrower. Before the email the treatment group already spent "
                  f"£{e['pre_period_check']['abs_diff']:.2f} more on average (p = {e['pre_period_check']['p_value']:.2f}), "
                  "a chance imbalance that inflates the unadjusted estimate; CUPED corrects for it."]
        (REPORTS / f"{e['name']}.md").write_text("\n".join(L) + "\n")


def write_results(exps, plan, peek0, peek1, aa) -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for e in exps:
        pr = e["primary"]
        rows.append({"experiment": e["name"], "title": e["title"], "users": e["users"], "primary_metric": pr["metric"],
                     "control": pr["control"], "treatment": pr["treatment"], "rel_change_pct": round(100 * pr["rel_diff"], 2),
                     "ci_low": pr["ci_low"], "ci_high": pr["ci_high"], "p_value": pr["p_value"],
                     "srm_p": e["srm"]["p_value"], "decision": e["decision"]})
    pd.DataFrame(rows).to_csv(RESULTS / "experiment_summary.csv", index=False)
    seg = [{"experiment": e["name"], **s} for e in exps if e["kind"] == "web" for s in e["segments"]]
    pd.DataFrame(seg).to_csv(RESULTS / "segments.csv", index=False)
    em = next(e for e in exps if e["kind"] == "email")
    summary = {
        "plan": plan,
        "experiments": {e["name"]: {"decision": e["decision"], "reason": e["reason"],
                                    "rel_change_pct": round(100 * e["primary"]["rel_diff"], 2),
                                    "p_value": e["primary"]["p_value"], "srm_p": e["srm"]["p_value"],
                                    "srm_share_t": e["srm"]["observed_share_t"],
                                    **({"p_better": e["bayes"]["p_treatment_better"]} if "bayes" in e else {})} for e in exps},
        "cuped": {"raw_effect": em["raw"]["abs_diff"], "raw_ci": [em["raw"]["ci_low"], em["raw"]["ci_high"]],
                  "cuped_effect": em["primary"]["abs_diff"], "cuped_ci": [em["primary"]["ci_low"], em["primary"]["ci_high"]],
                  "variance_reduction": em["variance_reduction"], "ci_width_reduction": em["ci_width_reduction"],
                  "pre_period_diff": em["pre_period_check"]["abs_diff"], "pre_period_p": em["pre_period_check"]["p_value"],
                  "true_effect": 0.60},
        "peeking": {k: v for k, v in peek0.items() if not isinstance(v, list)},
        "peeking_with_effect": {k: v for k, v in peek1.items() if not isinstance(v, list)},
        "aa_false_positive_rate": aa["false_positive_rate"],
        "widget_segments": [{k: s[k] for k in ("segment", "rel_diff", "p_value", "p_holm", "p_bh")}
                            for e in exps if e["name"] == "recommendations_widget" for s in e["segments"]],
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    return summary
