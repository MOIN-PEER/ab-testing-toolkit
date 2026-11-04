# Project summary: A/B Testing Toolkit

**Author:** Mohamed Moin Peer  |  **Type:** Experimentation and statistics  |  **Stack:** Python, NumPy, SciPy, statsmodels, pandas, matplotlib, JavaScript, pytest

## Problem
Companies run A/B tests to decide which changes to ship. Many tests are run badly: too small, stopped early, sliced into segments until something looks significant, or analysed despite a broken traffic split. The result is decisions based on noise.

## What I built
* **A reusable Python toolkit** covering the whole experiment lifecycle:
  * sample size and duration planning
  * sample-ratio-mismatch checks
  * z-tests, Welch t-tests and bootstrap
  * Bayesian P(better) and expected loss
  * CUPED variance reduction
  * Holm and Benjamini-Hochberg corrections
  * group-sequential boundaries for safe early looks
* **Explicit decision rules** that turn statistics into SHIP / DO NOT SHIP / INVESTIGATE / INCONCLUSIVE, and a Markdown decision report for each experiment.
* **A case study of five synthetic experiments with known true effects**, so every conclusion can be checked.
* **A browser calculator** for sample size, significance and SRM, ready to publish on GitHub Pages.
* **24 tests**, many checked against statsmodels and SciPy. Simulations verify the 5% false-positive rate.

## Results
* Planning: detecting a 10% lift on 3.2% conversion needs 49,774 visitors per group, which is 14 days.
* All five decisions match the built-in truth:
  * **checkout:** ship (+9.4%)
  * **free delivery:** no meaningful effect
  * **widget:** inconclusive; a segment "win" disappears after correction
  * **unit price:** investigate, because a tracking bug caused a sample ratio mismatch with p = 1.5×10⁻⁸
  * **email:** ship (+£0.52, true value £0.60)
* **CUPED** cut variance by 65% and narrowed the interval by 41%. It also corrected a chance pre-period imbalance that had inflated the raw estimate to £0.92.
* **Peeking daily** gives 21.6% false wins. Group-sequential boundaries restore 4.8% while keeping 77% power.

## Skills demonstrated
Experiment design · power analysis · frequentist and Bayesian inference · CUPED · SRM detection · multiple testing · sequential testing · simulation · decision-making under uncertainty · Python · JavaScript · testing.

## How to run
`pip install -r requirements.txt && pip install -e . && python -m ab_toolkit all && pytest`, then open `web/index.html`.
