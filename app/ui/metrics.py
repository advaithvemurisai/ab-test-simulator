"""Shared metric summaries for portfolio pages."""

from __future__ import annotations

import numpy as np
import pandas as pd
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


def summarize(data: pd.DataFrame) -> dict[str, object]:
    funded = conversion_ztest(data)
    revenue = revenue_ttest(data)
    revenue_ci = bootstrap_revenue_ci(data, n_boot=1_000)
    fraud = conversion_ztest(data, metric="fraud_flag")
    srm = srm_check(data)
    return {"funded": funded, "revenue": revenue, "revenue_ci": revenue_ci, "fraud": fraud, "srm": srm}
