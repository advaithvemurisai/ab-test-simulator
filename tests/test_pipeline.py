import numpy as np
from statsmodels.stats.proportion import proportions_ztest

from abtest.data import generate_experiment
from abtest.frequentist import conversion_ztest, srm_check


def test_generator_respects_seed_and_schema():
    first = generate_experiment(n_users=500, seed=123)
    second = generate_experiment(n_users=500, seed=123)
    assert first.equals(second)
    assert list(first.columns) == ["user_id", "day", "group", "device", "user_type", "converted", "revenue"]


def test_srm_fires_when_treatment_is_injected():
    data = generate_experiment(n_users=10_000, srm_injection=0.25, seed=4)
    result = srm_check(data)
    assert result["srm_detected"]
    assert result["treatment_count"] < result["control_count"]


def test_z_test_matches_statsmodels():
    data = generate_experiment(n_users=2_000, seed=99)
    result = conversion_ztest(data)
    treatment = data[data.group == "treatment"]["converted"]
    control = data[data.group == "control"]["converted"]
    expected = proportions_ztest([treatment.sum(), control.sum()], [len(treatment), len(control)])
    np.testing.assert_allclose([result["z_stat"], result["p_value"]], expected)
