"""Landing page: make the decision legible in 30 seconds."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from abtest.decision import decide
from abtest.frequentist import conversion_ztest, lift_decline_test
from abtest.impact import project_yearly_impact
from abtest.power import days_to_target_power, planned_power
from app.ui.context import get_context
from app.ui.metrics import summarize
from app.ui.theme import explain, inject_theme

PLANNED_MDE = 0.05

inject_theme()
data, scenario = get_context()
results = summarize(data)
funded = results["funded"]
revenue = results["revenue"]
revenue_ci = results["revenue_ci"]
fraud = results["fraud"]
srm = results["srm"]

midpoint = max(1, scenario.n_days // 2)
early_data, late_data = data[data.day <= midpoint], data[data.day > midpoint]
early, late = conversion_ztest(early_data), conversion_ztest(late_data)
n_per_arm = int(data.group.value_counts().min())
baseline = funded["control_rate"] or scenario.baseline_cr
verdict = decide(
    srm_p_value=srm["p_value"],
    funded_lift=funded["relative_lift"],
    funded_p_value=funded["p_value"],
    revenue_ci_low=revenue_ci["ci_low"],
    revenue_ci_high=revenue_ci["ci_high"],
    fraud_relative_lift=fraud["relative_lift"],
    fraud_p_value=fraud["p_value"],
    early_lift=early["relative_lift"],
    late_lift=late["relative_lift"],
    fade_p_value=lift_decline_test(early_data, late_data),
    planned_mde=PLANNED_MDE,
    current_power=planned_power(n_per_arm, baseline, PLANNED_MDE),
    additional_days=days_to_target_power(n_per_arm, len(data) / scenario.n_days, baseline, PLANNED_MDE),
)
impact = project_yearly_impact(
    data,
    revenue_ci=(revenue_ci["ci_low"], revenue_ci["ci_high"]),
    funded_ci=(
        funded["control_rate"] * results["funded_ci"][0],
        funded["control_rate"] * results["funded_ci"][1],
    ),
)

st.markdown('<div class="hero-copy"><div class="eyebrow">Experiment decision workspace</div><h1>LiftLab</h1><p>Should a neobank ship instant bank linking, or keep testing? LiftLab turns one experiment into a decision you can defend.</p></div>', unsafe_allow_html=True)
st.caption(f"Scenario: **{scenario.name}** · {scenario.description} {scenario.lesson}")

# "&#36;" stops Streamlit from reading dollar amounts as LaTeX math delimiters.
reasons_html = "".join(f"<p>• {reason.replace('$', '&#36;')}</p>" for reason in verdict.reasons)
st.markdown(f'<div class="verdict"><div class="eyebrow">Recommendation</div><h2>{verdict.label}</h2>{reasons_html}</div>', unsafe_allow_html=True)
if verdict.additional_days:
    st.info(f"Planning signal: at current traffic, collect roughly **{verdict.additional_days:,} more days** before revisiting the decision.")

st.subheader("Scorecard")
rows = [
    {"Metric": "Funded-account rate", "Role": "Primary", "Control": f"{funded['control_rate']:.2%}", "Treatment": f"{funded['treatment_rate']:.2%}", "Lift (95% CI)": f"{results['funded_ci'][0]:.1%} to {results['funded_ci'][1]:.1%}", "p-value": f"{funded['p_value']:.3f}", "Status": "Positive" if funded["p_value"] < .05 and funded["relative_lift"] > 0 else "Unclear"},
    {"Metric": "Net revenue / visitor", "Role": "Value", "Control": f"${revenue['control_mean']:.2f}", "Treatment": f"${revenue['treatment_mean']:.2f}", "Lift (95% CI)": f"${revenue_ci['ci_low']:.2f} to ${revenue_ci['ci_high']:.2f}", "p-value": f"{revenue['p_value']:.3f}", "Status": "Healthy" if revenue_ci["ci_low"] >= 0 else "Downside"},
    {"Metric": "Fraud rate", "Role": "Guardrail", "Control": f"{fraud['control_rate'] * 10_000:.1f} / 10k", "Treatment": f"{fraud['treatment_rate'] * 10_000:.1f} / 10k", "Lift (95% CI)": f"{results['fraud_ci'][0]:.1%} to {results['fraud_ci'][1]:.1%}" if results['fraud_ci'][0] == results['fraud_ci'][0] else "n/a: zero control events", "p-value": f"{fraud['p_value']:.3f}", "Status": "Guardrail" if fraud["p_value"] < .05 and fraud["relative_lift"] > .5 else "Pass"},
    {"Metric": "Traffic split", "Role": "Validity", "Control": f"{srm['control_count']:,}", "Treatment": f"{srm['treatment_count']:,}", "Lift (95% CI)": "50 / 50 planned", "p-value": f"{srm['p_value']:.3f}", "Status": "Check" if srm["srm_detected"] else "Pass"},
]
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

st.subheader("Projected yearly impact")
cols = st.columns(3)
cols[0].metric("Funded accounts", f"{impact['funded_accounts_delta']:+,.0f}", "at 500k visitors/month")
cols[1].metric("Net revenue", f"${impact['revenue_delta']:+,.0f}", f"range ${impact['revenue_range'][0]:+,.0f} to ${impact['revenue_range'][1]:+,.0f}")
cols[2].metric("Fraud cases", f"{impact['fraud_cases_delta']:+,.0f}", "incremental cases")

st.markdown('<div class="skill-strip">' + ''.join(f'<span class="skill">{skill}</span>' for skill in ["Experiment design", "Power analysis", "Guardrails", "SRM diagnosis", "Sequential testing", "Bayesian inference", "Multiple-testing correction"]) + '</div>', unsafe_allow_html=True)

with st.expander("Metric glossary"):
    explain("p-value", "A gap this large would show up by chance about p × 100% of the time if the change did nothing.", "Two-sided two-proportion z-test for the binary outcome.")
    explain("95% confidence interval", "The range of effects compatible with the observed data under repeated sampling.", "Bootstrap percentile interval for revenue; Wilson-derived approximation for binary rates.")
    explain("SRM", "A traffic split check: did the 50/50 assignment actually come out 50/50?", "Chi-square goodness-of-fit test against the planned allocation.")
