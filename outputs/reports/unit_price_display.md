# Experiment report: Show price per unit

*Synthetic data (fictional retailer Lagan Living).*

**Decision: INVESTIGATE**. Sample ratio mismatch: treatment got 49.1% of users instead of 50% (p = 1.5e-08). Fix tracking and re-run; do not use this result.

## Design
* Change: Unit price shown under the main price.
* Hypothesis: Showing price per unit on multipacks will raise conversion.
* Users analysed: 98,104
* Planned before launch: detect a 10% relative lift on a 3.2% conversion rate with 80% power at alpha 0.05, so 49,774 visitors per group over 14 days.

## Health check: sample ratio
* Control 49,939 / treatment 48,165 (49.10% treatment, expected 50%), chi-square p = 1.48e-08: **MISMATCH, do not trust the results below**.

## Results

| Metric | Control | Treatment | Change | 95% CI (absolute) | p-value | Method |
|---|---|---|---|---|---|---|
| Conversion rate | 3.28% | 3.59% | +9.6% | +0.0008577 to +0.005419 | 0.00695 | two-proportion z-test |
| Revenue per visitor (£) | £2.01 | £2.16 | +7.5% | -0.03072 to +0.3377 | 0.118 | bootstrap (percentile) |
| Average order value (£) | £61.33 | £60.18 | -1.9% | -4.755 to +2.459 | 0.533 | Welch t-test |
| Return rate | 8.00% | 8.61% | +7.6% | -0.01254 to +0.02475 | 0.522 | two-proportion z-test |

Bayesian check (Beta(1,1) prior): P(treatment better) = 99.6%, median lift +9.6% (95% credible interval +2.5% to +17.1%).

## Segments (exploratory, adjusted for 4 comparisons)

| Segment | Change | p-value | Holm-adjusted | BH-adjusted |
|---|---|---|---|---|
| desktop / new | +19.6% | 0.020 | 0.061 | 0.040 |
| desktop / returning | -6.3% | 0.278 | 0.556 | 0.371 |
| mobile / new | +2.6% | 0.749 | 0.749 | 0.749 |
| mobile / returning | +22.3% | 0.001 | 0.004 | 0.004 |
