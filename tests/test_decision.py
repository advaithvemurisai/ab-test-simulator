import pandas as pd

from abtest.decision import decide
from abtest.impact import project_yearly_impact
from abtest.scenarios import SCENARIOS, get_scenario


def test_scenarios_are_reproducible_and_named():
    assert list(SCENARIOS) == [
        "Growth vs. fraud",
        "Clear winner",
        "Too small to tell",
        "Broken rollout",
        "Shiny-new effect",
    ]
    assert get_scenario("Broken rollout").srm_injection == 0.15


def test_decision_prioritizes_validity_and_guardrails():
    invalid = decide(srm_p_value=0.0001, funded_lift=.3, funded_p_value=.001, revenue_ci_low=1, revenue_ci_high=2, fraud_relative_lift=0, fraud_p_value=1)
    guardrail = decide(srm_p_value=.4, funded_lift=.3, funded_p_value=.001, revenue_ci_low=1, revenue_ci_high=2, fraud_relative_lift=.8, fraud_p_value=.01)
    assert invalid.label == "DON'T TRUST"
    assert guardrail.label == "DON'T SHIP"


def test_decision_can_ship_or_keep_testing():
    ship = decide(srm_p_value=.4, funded_lift=.1, funded_p_value=.01, revenue_ci_low=-1, revenue_ci_high=1, fraud_relative_lift=.1, fraud_p_value=.4)
    keep_testing = decide(srm_p_value=.4, funded_lift=.02, funded_p_value=.4, revenue_ci_low=1, revenue_ci_high=2, fraud_relative_lift=.1, fraud_p_value=.4)
    assert ship.label == "SHIP"
    assert keep_testing.label == "KEEP TESTING"
    assert keep_testing.additional_days > 0


def test_revenue_only_rejects_when_the_full_interval_is_negative():
    noisy = decide(srm_p_value=.4, funded_lift=.1, funded_p_value=.01, revenue_ci_low=-1, revenue_ci_high=1, fraud_relative_lift=.1, fraud_p_value=.4)
    negative = decide(srm_p_value=.4, funded_lift=.1, funded_p_value=.01, revenue_ci_low=-2, revenue_ci_high=-.5, fraud_relative_lift=.1, fraud_p_value=.4)
    assert noisy.label == "SHIP"
    assert negative.label == "DON'T SHIP"


def test_impact_scales_to_annual_traffic():
    data = pd.DataFrame({"group": ["control", "control", "treatment", "treatment"], "converted": [False, False, True, True], "revenue": [1.0, 1.0, 2.0, 2.0], "fraud_flag": [False, False, False, False]})
    impact = project_yearly_impact(data, monthly_visitors=100)
    assert impact["funded_accounts_delta"] == 1_200.0
    assert impact["revenue_delta"] == 1_200.0
    assert impact["funded_accounts_range"] == (1_200.0, 1_200.0)


def test_impact_funded_range_uses_supplied_interval():
    data = pd.DataFrame({"group": ["control", "treatment"], "converted": [False, True], "revenue": [0.0, 0.0], "fraud_flag": [False, False]})
    impact = project_yearly_impact(data, monthly_visitors=100, funded_ci=(.005, .015))
    assert impact["funded_accounts_range"] == (6.0, 18.0)
