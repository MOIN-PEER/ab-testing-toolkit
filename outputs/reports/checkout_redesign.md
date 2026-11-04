# Experiment report: One-page checkout redesign

*Synthetic data (fictional retailer Lagan Living).*

**Decision: SHIP**. Conversion rate up +9.4% (95% CI +0.0008326 to +0.005356, p = 0.00732); guardrails fine.

## Design
* Change: Checkout reduced from three steps to one page.
* Hypothesis: A shorter, one-page checkout will raise the share of visitors who buy.
* Users analysed: 100,000
* Planned before launch: detect a 10% relative lift on a 3.2% conversion rate with 80% power at alpha 0.05, so 49,774 visitors per group over 14 days.

## Health check: sample ratio
* Control 50,257 / treatment 49,743 (49.74% treatment, expected 50%), chi-square p = 0.104: OK.

## Results

| Metric | Control | Treatment | Change | 95% CI (absolute) | p-value | Method |
|---|---|---|---|---|---|---|
| Conversion rate | 3.29% | 3.60% | +9.4% | +0.0008326 to +0.005356 | 0.00732 | two-proportion z-test |
| Revenue per visitor (£) | £2.09 | £2.18 | +4.4% | -0.08963 to +0.2677 | 0.313 | bootstrap (percentile) |
| Average order value (£) | £63.37 | £60.48 | -4.6% | -6.356 to +0.5812 | 0.103 | Welch t-test |
| Return rate | 8.04% | 8.15% | +1.4% | -0.01711 to +0.01933 | 0.905 | two-proportion z-test |

Bayesian check (Beta(1,1) prior): P(treatment better) = 99.6%, median lift +9.4% (95% credible interval +2.5% to +16.8%).

## Segments (exploratory, adjusted for 4 comparisons)

| Segment | Change | p-value | Holm-adjusted | BH-adjusted |
|---|---|---|---|---|
| desktop / new | +13.0% | 0.119 | 0.359 | 0.238 |
| desktop / returning | +10.9% | 0.090 | 0.359 | 0.238 |
| mobile / new | +7.3% | 0.345 | 0.399 | 0.345 |
| mobile / returning | +7.8% | 0.200 | 0.399 | 0.266 |
