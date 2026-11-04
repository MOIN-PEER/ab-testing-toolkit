# Experiment report: Personalised email subject line

*Synthetic data (fictional retailer Lagan Living).*

**Decision: SHIP**. 30-day spend (£), CUPED up +2.3% (95% CI +0.2365 to +0.8031, p = 0.000324); guardrails fine.

## Design
* Change: Subject line includes the member's first name and last category viewed.
* Hypothesis: A personalised subject line will raise 30-day spend of loyalty members.
* Users analysed: 40,000

## Health check: sample ratio
* Control 20,059 / treatment 19,941 (49.85% treatment, expected 50%), chi-square p = 0.555: OK.

## Results

| Metric | Control | Treatment | Change | 95% CI (absolute) | p-value | Method |
|---|---|---|---|---|---|---|
| 30-day spend (£), CUPED | £22.73 | £23.25 | +2.3% | +0.2365 to +0.8031 | 0.000324 | Welch t-test |
| 30-day spend (£), unadjusted | £22.53 | £23.45 | +4.1% | +0.4418 to +1.397 | 0.000161 | Welch t-test |
| Open rate | 24.69% | 28.90% | +17.1% | +0.03346 to +0.0508 | 1.84e-21 | two-proportion z-test |

CUPED used each member's spend in the 30 days before the email (theta = 0.848). It removed 65% of the variance and made the confidence interval 41% narrower. Before the email the treatment group already spent £0.47 more on average (p = 0.04), a chance imbalance that inflates the unadjusted estimate; CUPED corrects for it.
