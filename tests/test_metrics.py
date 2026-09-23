import pandas as pd
from numpy import isnan

from abtest.power import observed_power
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


def test_observed_power_is_calculated_from_the_observed_effect():
    weak = pd.DataFrame(
        {
            "group": ["control"] * 100 + ["treatment"] * 100,
            "converted": [True] * 10 + [False] * 90 + [True] * 11 + [False] * 89,
        }
    )
    strong = pd.DataFrame(
        {
            "group": ["control"] * 1_000 + ["treatment"] * 1_000,
            "converted": [True] * 40 + [False] * 960 + [True] * 80 + [False] * 920,
        }
    )
    assert 0 <= observed_power(weak) <= 1
    assert observed_power(strong) > observed_power(weak)
