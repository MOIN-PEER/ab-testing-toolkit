# Experiment report: 'You may also like' widget

*Synthetic data (fictional retailer Lagan Living).*

**Decision: INCONCLUSIVE**. Not significant (p = 0.12); the 95% CI (-0.0004633 to +0.003969) still includes effects worth having. Do not ship on this evidence.

## Design
* Change: Recommendation carousel added to the basket page.
* Hypothesis: Product recommendations on the basket page will raise conversion.
* Users analysed: 100,000
* Planned before launch: detect a 10% relative lift on a 3.2% conversion rate with 80% power at alpha 0.05, so 49,774 visitors per group over 14 days.

## Health check: sample ratio
* Control 50,161 / treatment 49,839 (49.84% treatment, expected 50%), chi-square p = 0.309: OK.

## Results

| Metric | Control | Treatment | Change | 95% CI (absolute) | p-value | Method |
|---|---|---|---|---|---|---|
| Conversion rate | 3.22% | 3.39% | +5.4% | -0.0004633 to +0.003969 | 0.121 | two-proportion z-test |
| Revenue per visitor (£) | £1.99 | £2.13 | +6.8% | -0.05149 to +0.3175 | 0.152 | bootstrap (percentile) |
| Average order value (£) | £61.99 | £62.78 | +1.3% | -3.007 to +4.595 | 0.682 | Welch t-test |
| Return rate | 8.36% | 8.57% | +2.5% | -0.01688 to +0.02109 | 0.828 | two-proportion z-test |

Bayesian check (Beta(1,1) prior): P(treatment better) = 94.0%, median lift +5.5% (95% credible interval -1.4% to +12.7%).

## Segments (exploratory, adjusted for 4 comparisons)

| Segment | Change | p-value | Holm-adjusted | BH-adjusted |
|---|---|---|---|---|
| desktop / new | +3.3% | 0.687 | 1.000 | 0.949 |
| desktop / returning | +2.0% | 0.738 | 1.000 | 0.949 |
| mobile / new | +19.4% | 0.020 | 0.081 | 0.081 |
| mobile / returning | +0.4% | 0.949 | 1.000 | 0.949 |
