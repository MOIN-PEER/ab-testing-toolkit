import numpy as np
import pytest
from scipy import stats as sps
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportions_ztest

from ab_toolkit import stats as S


def test_ztest_matches_statsmodels():
    r = S.two_proportion_ztest(1655, 50257, 1792, 49743)
    z, p = proportions_ztest([1792, 1655], [49743, 50257])
    assert r.p_value == pytest.approx(p, rel=1e-6)
    assert r.ci_low < r.abs_diff < r.ci_high and r.significant


def test_welch_matches_scipy():
    rng = np.random.default_rng(1)
    a, b = rng.normal(10, 2, 500), rng.normal(10.4, 3, 700)
    r = S.welch_ttest(a, b)
    assert r.p_value == pytest.approx(sps.ttest_ind(b, a, equal_var=False).pvalue)


def test_bootstrap_ci_contains_true_difference():
    rng = np.random.default_rng(2)
    a, b = rng.lognormal(3, 1, 3000), rng.lognormal(3, 1, 3000) * 1.10
    r = S.bootstrap_diff(a, b, n_boot=800)
    true = np.exp(3 + 0.5) * 0.10
    assert r.ci_low < true < r.ci_high


def test_bayes_probability_direction():
    strong = S.bayes_proportions(1000, 50000, 1200, 50000)
    none = S.bayes_proportions(1000, 50000, 1000, 50000)
    assert strong["p_treatment_better"] > 0.99
    assert 0.4 < none["p_treatment_better"] < 0.6
    assert strong["expected_loss_ship_treatment"] < strong["expected_loss_keep_control"]


def test_cuped_reduces_variance_and_is_unbiased():
    rng = np.random.default_rng(3)
    n = 20000
    x = rng.gamma(2, 10, n)
    g = rng.random(n) < 0.5
    y = 0.8 * x + rng.normal(0, 8, n) + np.where(g, 1.0, 0.0)
    adj, theta = S.cuped(y, x)
    assert adj.var() < 0.5 * y.var() and theta == pytest.approx(0.8, abs=0.05)
    assert adj[g].mean() - adj[~g].mean() == pytest.approx(1.0, abs=0.3)


def test_srm_flags_bad_split_only():
    assert not S.srm_check(50100, 49900)["srm_detected"]
    assert S.srm_check(49939, 48165)["srm_detected"]


@pytest.mark.parametrize("method,sm", [("bonferroni", "bonferroni"), ("holm", "holm"), ("bh", "fdr_bh")])
def test_pvalue_adjustments_match_statsmodels(method, sm):
    p = [0.01, 0.04, 0.03, 0.20, 0.002]
    assert np.allclose(S.adjust_pvalues(p, method), multipletests(p, method=sm)[1])
