import pytest

from ab_toolkit import analysis as A
from ab_toolkit.generate_data import generate
from ab_toolkit.sequential import obf_boundaries, peeking_simulation


@pytest.fixture(scope="module")
def data():
    return generate()


@pytest.mark.parametrize("name,expected", [("checkout_redesign", "SHIP"), ("free_delivery_30", "NO MEANINGFUL EFFECT"),
                                           ("recommendations_widget", "INCONCLUSIVE"), ("unit_price_display", "INVESTIGATE")])
def test_web_decisions_match_known_truth(data, name, expected):
    assert A.analyse_web(name, data[name])["decision"] == expected


def test_email_cuped_closer_to_truth_and_narrower(data):
    e = A.analyse_email(data["email_subject_line"])
    raw, cup = e["raw"], e["primary"]
    assert abs(cup["abs_diff"] - 0.60) < abs(raw["abs_diff"] - 0.60)
    assert (cup["ci_high"] - cup["ci_low"]) < 0.7 * (raw["ci_high"] - raw["ci_low"])
    assert e["decision"] == "SHIP"


def test_null_segment_false_positive_removed_by_adjustment(data):
    segs = A.analyse_web("recommendations_widget", data["recommendations_widget"])["segments"]
    assert any(s["p_value"] < 0.05 for s in segs)
    assert all(s["p_holm"] >= 0.05 for s in segs)


def test_decide_rules():
    from ab_toolkit.stats import Result
    ok = {"srm_detected": False}
    up = Result("m", 0.03, 0.033, 0.003, 0.1, 0.001, 0.005, 0.01, "z", 1, 1)
    assert A.decide(up, ok, [])[0] == "SHIP"
    assert A.decide(up, {"srm_detected": True, "observed_share_t": 0.48, "p_value": 1e-9}, [])[0] == "INVESTIGATE"
    assert A.decide(up, ok, [{"metric": "Return rate", "worse": True}])[0] == "DO NOT SHIP"


def test_aa_false_positive_rate_near_alpha():
    assert 0.035 < A.aa_validation(n_sims=1500)["false_positive_rate"] < 0.065


def test_peeking_inflates_errors_and_sequential_fixes_it():
    r = peeking_simulation(sims=2500)
    assert r["peek_every_day_rate"] > 0.15
    assert 0.03 < r["group_sequential_rate"] < 0.07
    b = obf_boundaries(5)
    assert b[0] > b[-1] > 1.96
