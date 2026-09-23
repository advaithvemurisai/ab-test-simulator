"""Business impact projections from experiment estimates."""

from __future__ import annotations

import pandas as pd


def project_yearly_impact(
    data: pd.DataFrame,
    monthly_visitors: int = 500_000,
    revenue_ci: tuple[float, float] | None = None,
    fraud_tolerance: float = 0.50,
) -> dict[str, float | tuple[float, float]]:
    """Project incremental annual outcomes at a stated monthly traffic level."""
    control = data[data.group == "control"]
    treatment = data[data.group == "treatment"]
    control_rate = control.converted.mean()
    treatment_rate = treatment.converted.mean()
    control_revenue = control.revenue.mean()
    treatment_revenue = treatment.revenue.mean()
    control_fraud = control.fraud_flag.mean()
    treatment_fraud = treatment.fraud_flag.mean()
    annual_visitors = monthly_visitors * 12
    funded_delta = (treatment_rate - control_rate) * annual_visitors
    revenue_delta = (treatment_revenue - control_revenue) * annual_visitors
    fraud_delta = (treatment_fraud - control_fraud) * annual_visitors
    if revenue_ci is None:
        revenue_range = (revenue_delta, revenue_delta)
    else:
        revenue_range = (revenue_ci[0] * annual_visitors, revenue_ci[1] * annual_visitors)
    return {
        "monthly_visitors": float(monthly_visitors),
        "funded_accounts_delta": float(funded_delta),
        "funded_accounts_range": (float(funded_delta), float(funded_delta)),
        "revenue_delta": float(revenue_delta),
        "revenue_range": revenue_range,
        "fraud_cases_delta": float(fraud_delta),
        "fraud_tolerance": float(fraud_tolerance),
    }
