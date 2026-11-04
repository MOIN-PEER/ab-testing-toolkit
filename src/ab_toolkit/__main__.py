"""Command line:

    python -m ab_toolkit data       # generate the synthetic experiment logs -> data/
    python -m ab_toolkit analyse    # analyse all experiments -> outputs/ (reports, figures, results)
    python -m ab_toolkit all        # both
    python -m ab_toolkit plan --baseline 0.032 --mde 0.10 --daily 7143   # sample-size calculator
"""

import argparse
import sys


def main() -> None:
    ap = argparse.ArgumentParser(prog="ab_toolkit")
    ap.add_argument("cmd", nargs="?", default="all", choices=["data", "analyse", "all", "plan"])
    ap.add_argument("--baseline", type=float, default=0.032)
    ap.add_argument("--mde", type=float, default=0.10, help="relative lift, e.g. 0.10 for +10%%")
    ap.add_argument("--daily", type=float, default=7143, help="eligible visitors per day")
    a = ap.parse_args()
    if a.cmd == "plan":
        from . import power as P
        n = P.sample_size_proportion(a.baseline, a.mde)
        print(f"Baseline {a.baseline:.2%}, detect {a.mde:+.0%} relative (to {a.baseline * (1 + a.mde):.2%}) "
              f"with 80% power, alpha 0.05:\n  {n:,} visitors per group, {2 * n:,} in total, "
              f"about {P.duration_days(n, a.daily)} days at {a.daily:,.0f} visitors a day")
        return
    if a.cmd in ("data", "all"):
        from .generate_data import write
        d = write()
        print("Data: " + ", ".join(f"{k} ({len(v):,})" for k, v in d.items()))
    if a.cmd in ("analyse", "all"):
        from . import analysis as A
        from . import reporting as R
        from .generate_data import load
        from .sequential import peeking_simulation
        d = load()
        plan = A.plan()
        exps = [A.analyse_web(k, d[k]) for k in ("checkout_redesign", "free_delivery_30", "recommendations_widget", "unit_price_display")]
        exps.append(A.analyse_email(d["email_subject_line"]))
        peek0, peek1 = peeking_simulation(lift=0.0), peeking_simulation(lift=0.10)
        aa = A.aa_validation()
        R.figures(exps, peek0, peek1, aa)
        R.write_reports(exps, plan)
        R.write_results(exps, plan, peek0, peek1, aa)
        for e in exps:
            print(f"  {e['title']:<36} {e['decision']}")
        print(f"Peeking daily: {100 * peek0['peek_every_day_rate']:.1f}% false wins; group-sequential: "
              f"{100 * peek0['group_sequential_rate']:.1f}%")
        print("Reports: outputs/reports  ·  Figures: outputs/figures  ·  Results: outputs/results")


if __name__ == "__main__":
    sys.exit(main())
