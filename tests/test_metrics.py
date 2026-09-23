import numpy as np
import pandas as pd
from numpy import isnan

from abtest.power import analytic_sample_size, days_to_target_power, planned_power, simulate_power
from app.ui.metrics import relative_lift_ci, summarize


def test_relative_lift_ci_returns_bounds_for_binary_metric():
    data = pd.DataFrame(
        {
            "group": ["control"] * 100 + ["treatment"] * 100,
            "converted": [True] * 10 + [False] * 90 + [True] * 20 + [False] * 80,
            "fraud_flag": [False] * 200,
            "revenue": [0.0] * 200,
        }
    )
    low, high = relative_lift_ci(data, "converted")
    assert low < 1.0 < high
    assert summarize(data)["funded_ci"] == (low, high)


def test_zero_control_events_are_explicitly_not_estimable():
    data = pd.DataFrame(
        {
            "group": ["control"] * 10 + ["treatment"] * 10,
            "converted": [False] * 20,
            "fraud_flag": [False] * 20,
            "revenue": [0.0] * 20,
        }
    )
    low, high = relative_lift_ci(data, "fraud_flag")
    assert isnan(low) and isnan(high)


def test_planned_power_and_days_use_the_planned_lift_not_the_observed_one():
    required = analytic_sample_size(0.04, 0.05)
    assert abs(planned_power(required, 0.04, 0.05) - 0.80) < 0.01
    assert planned_power(2_500, 0.04, 0.05) < 0.2
    assert days_to_target_power(required, 1_000, 0.04, 0.05) == 0
    assert days_to_target_power(2_500, 1_000, 0.04, 0.05) == int(np.ceil(2 * (required - 2_500) / 1_000))


def test_simulated_power_matches_theory():
    required = analytic_sample_size(0.04, 0.05)
    assert abs(simulate_power(required, 0.04, 0.05, simulations=4_000, seed=3) - 0.80) < 0.03
    assert simulate_power(required, 0.04, 0.0, simulations=4_000, seed=3) < 0.07
