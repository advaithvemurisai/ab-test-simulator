import numpy as np
from statsmodels.stats.proportion import proportions_ztest

from abtest.data import generate_experiment
from abtest.frequentist import conversion_ztest, srm_check


def test_generator_respects_seed_and_schema():
    first = generate_experiment(n_users=500, seed=123)
    second = generate_experiment(n_users=500, seed=123)
    assert first.equals(second)
    assert list(first.columns) == [
        "user_id", "day", "weekday", "group", "device", "channel", "customer_type",
        "started_application", "kyc_passed", "bank_linked", "converted",
        "initial_deposit", "fraud_flag", "revenue",
    ]


def test_funnel_steps_are_nested_and_deposits_are_realistic():
    data = generate_experiment(n_users=50_000, seed=7)
    assert (data.kyc_passed <= data.started_application).all()
    assert (data.bank_linked <= data.kyc_passed).all()
    assert (data.converted <= data.bank_linked).all()
    assert (data.fraud_flag <= data.converted).all()
    funded = data.loc[data.converted, "initial_deposit"]
    assert funded.between(10, 250_000).all()
    assert funded.mean() > 1.5 * funded.median()
    assert (data.loc[~data.converted, "initial_deposit"] == 0).all()


def test_average_lift_and_fraud_uplift_are_recovered():
    data = generate_experiment(n_users=1_000_000, relative_lift=0.20, fraud_uplift=1.0, seed=11)
    assert abs(conversion_ztest(data)["relative_lift"] - 0.20) < 0.04
    assert conversion_ztest(data, metric="fraud_flag")["relative_lift"] > 0.5
    assert (data.loc[data.fraud_flag, "revenue"] < 0).all()


def test_srm_fires_when_treatment_is_injected():
    data = generate_experiment(n_users=10_000, srm_injection=0.25, seed=4)
    result = srm_check(data)
    assert result["srm_detected"]
    assert result["treatment_count"] < result["control_count"]
    share = data.groupby("device")["group"].apply(lambda g: g.eq("treatment").mean())
    assert share.idxmin() == "android"


def test_z_test_matches_statsmodels():
    data = generate_experiment(n_users=2_000, seed=99)
    result = conversion_ztest(data)
    treatment = data[data.group == "treatment"]["converted"]
    control = data[data.group == "control"]["converted"]
    expected = proportions_ztest([treatment.sum(), control.sum()], [len(treatment), len(control)])
    np.testing.assert_allclose([result["z_stat"], result["p_value"]], expected)
