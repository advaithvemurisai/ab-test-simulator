"""Shared metric summaries for portfolio pages."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.proportion import proportion_confint

from abtest.frequentist import bootstrap_revenue_ci, conversion_ztest, revenue_ttest, srm_check


def proportion_difference_ci(data: pd.DataFrame, metric: str, confidence: float = .95) -> tuple[float, float]:
    control = data[data.group == "control"][metric].astype(bool)
    treatment = data[data.group == "treatment"][metric].astype(bool)
    control_rate = control.mean()
    treatment_rate = treatment.mean()
    control_ci = proportion_confint(control.sum(), len(control), alpha=1 - confidence, method="wilson")
    treatment_ci = proportion_confint(treatment.sum(), len(treatment), alpha=1 - confidence, method="wilson")
    return float(treatment_rate - control_rate - np.sqrt((treatment_ci[1] - treatment_ci[0]) ** 2 + (control_ci[1] - control_ci[0]) ** 2) / 2), float(treatment_rate - control_rate + np.sqrt((treatment_ci[1] - treatment_ci[0]) ** 2 + (control_ci[1] - control_ci[0]) ** 2) / 2)


def relative_lift_ci(data: pd.DataFrame, metric: str, confidence: float = .95) -> tuple[float, float]:
    """Return a delta-method CI for treatment/control - 1."""
    control = data[data.group == "control"][metric].astype(bool)
    treatment = data[data.group == "treatment"][metric].astype(bool)
    control_rate = control.mean()
    treatment_rate = treatment.mean()
    if control_rate == 0:
        return (float("nan"), float("nan"))
    z_value = norm.ppf(1 - (1 - confidence) / 2)
    variance = (
        treatment_rate * (1 - treatment_rate) / max(len(treatment), 1) / control_rate**2
        + control_rate * (1 - control_rate) / max(len(control), 1) * treatment_rate**2 / control_rate**4
    )
    estimate = treatment_rate / control_rate - 1
    margin = z_value * np.sqrt(variance)
    return float(estimate - margin), float(estimate + margin)


def summarize(data: pd.DataFrame) -> dict[str, object]:
    funded = conversion_ztest(data)
    revenue = revenue_ttest(data)
    revenue_ci = bootstrap_revenue_ci(data, n_boot=1_000)
    fraud = conversion_ztest(data, metric="fraud_flag")
    srm = srm_check(data)
    return {
        "funded": funded,
        "funded_ci": relative_lift_ci(data, "converted"),
        "revenue": revenue,
        "revenue_ci": revenue_ci,
        "fraud": fraud,
        "fraud_ci": relative_lift_ci(data, "fraud_flag"),
        "srm": srm,
    }
