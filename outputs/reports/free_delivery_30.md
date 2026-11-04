# Experiment report: Free delivery from £30 (was £40)

*Synthetic data (fictional retailer Lagan Living).*

**Decision: NO MEANINGFUL EFFECT**. Not significant, and the 95% CI rules out a lift as large as the one we planned for. A smaller lift cannot be excluded, but it would not justify the change on its own.

## Design
* Change: Free-delivery threshold lowered from £40 to £30.
* Hypothesis: A lower free-delivery threshold will raise conversion without cutting revenue.
* Users analysed: 100,000
* Planned before launch: detect a 10% relative lift on a 3.2% conversion rate with 80% power at alpha 0.05, so 49,774 visitors per group over 14 days.

## Health check: sample ratio
* Control 50,021 / treatment 49,979 (49.98% treatment, expected 50%), chi-square p = 0.894: OK.

## Results

| Metric | Control | Treatment | Change | 95% CI (absolute) | p-value | Method |
|---|---|---|---|---|---|---|
| Conversion rate | 3.33% | 3.39% | +1.6% | -0.001706 to +0.002762 | 0.643 | two-proportion z-test |
| Revenue per visitor (£) | £2.06 | £2.01 | -2.3% | -0.2317 to +0.1366 | 0.603 | bootstrap (percentile) |
| Average order value (£) | £61.70 | £59.34 | -3.8% | -6.215 to +1.49 | 0.229 | Welch t-test |
| Return rate | 6.65% | 7.74% | +16.3% | -0.006635 to +0.0283 | 0.225 | two-proportion z-test |

Bayesian check (Beta(1,1) prior): P(treatment better) = 67.8%, median lift +1.6% (95% credible interval -4.9% to +8.6%).

## Segments (exploratory, adjusted for 4 comparisons)

| Segment | Change | p-value | Holm-adjusted | BH-adjusted |
|---|---|---|---|---|
| desktop / new | +3.4% | 0.661 | 1.000 | 0.986 |
| desktop / returning | -1.6% | 0.787 | 1.000 | 0.986 |
| mobile / new | +5.8% | 0.455 | 1.000 | 0.986 |
| mobile / returning | +0.1% | 0.986 | 1.000 | 0.986 |
