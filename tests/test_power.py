import math

import pytest
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from ab_toolkit import power as P


def test_sample_size_close_to_statsmodels():
    ours = P.sample_size_proportion(0.032, 0.10)
    es = proportion_effectsize(0.032 * 1.1, 0.032)
    sm = NormalIndPower().solve_power(es, alpha=0.05, power=0.8, ratio=1)
    assert abs(ours - sm) / sm < 0.02          # arcsine vs normal approximation: within 2%


def test_sample_size_monotonic():
    assert P.sample_size_proportion(0.032, 0.05) > P.sample_size_proportion(0.032, 0.10) > P.sample_size_proportion(0.032, 0.20)
    assert P.sample_size_proportion(0.05, 0.10) < P.sample_size_proportion(0.02, 0.10)


def test_mde_inverts_sample_size():
    n = P.sample_size_proportion(0.032, 0.10)
    assert P.mde_proportion(0.032, n) == pytest.approx(0.10, abs=0.002)
    assert P.achieved_power(0.032, 0.10, n) == pytest.approx(0.80, abs=0.01)


def test_duration_rounds_up_to_weeks():
    assert P.duration_days(49_774, 7_143) == 14
    assert P.duration_days(1_000, 100_000) == 7
    assert P.duration_days(60_000, 7_143) % 7 == 0


def test_mean_sample_size_formula():
    assert P.sample_size_mean(10, 1) == math.ceil((1.959964 + 0.841621) ** 2 * 100 * 2)


def test_invalid_rates():
    with pytest.raises(ValueError):
        P.sample_size_proportion(0.95, 0.10)
