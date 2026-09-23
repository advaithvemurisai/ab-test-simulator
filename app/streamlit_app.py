"""Interactive A/B test simulator dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from abtest.bayesian import bayesian_comparison, beta_binomial
from abtest.data import generate_experiment
from abtest.frequentist import (
    benjamini_hochberg,
    bootstrap_revenue_ci,
    conversion_ztest,
    revenue_ttest,
    srm_check,
)
from abtest.power import analytic_sample_size, mde_curve, power_curve
from abtest.sequential import alpha_spending_boundary, sequential_aa_simulation

st.set_page_config(page_title="A/B Test Simulator", page_icon="📈", layout="wide")
st.title("A/B Test Simulator: Savings Account Onboarding")
st.caption(
    "A neobank tests **instant bank linking** (treatment) against **micro-deposit verification** "
    "(control) in its high-yield savings sign-up flow. Primary metric: funded accounts. "
    "Value metric: 90-day net revenue (interest margin on balances minus fraud losses). "
    "Guardrail: first-party fraud from returned deposits."
)

with st.sidebar:
    st.header("Experiment controls")
    n_users = st.number_input("Visitors randomized", min_value=200, max_value=100_000, value=20_000, step=500)
    baseline_cr = st.slider("Baseline funded-account rate", 0.005, 0.20, 0.04, 0.005, format="%.3f")
    relative_lift = st.slider("True lift in funded accounts", -0.50, 1.00, 0.05, 0.01, format="%.0%")
    fraud_uplift = st.slider("Fraud increase from instant linking", 0.0, 2.0, 0.30, 0.05, format="%.0%")
    n_days = st.slider("Experiment days", 3, 30, 14)
    seed = st.number_input("Seed", min_value=0, value=42, step=1)
    novelty = st.checkbox("Apply novelty decay")
    srm_injection = st.slider("Treatment visitors lost (SRM injection)", 0.0, 0.30, 0.0, 0.01, format="%.0%")

@st.cache_data
def load_data(users: int, cr: float, lift: float, days: int, random_seed: int, novelty_effect: bool, srm: float, fraud: float):
    return generate_experiment(users, baseline_cr=cr, relative_lift=lift, n_days=days, seed=random_seed, novelty_effect=novelty_effect, srm_injection=srm, fraud_uplift=fraud)


data = load_data(n_users, baseline_cr, relative_lift, n_days, seed, novelty, srm_injection, fraud_uplift)
frequentist = conversion_ztest(data)
srm = srm_check(data)
data_tab, power_tab, frequentist_tab, peeking_tab, bayesian_tab = st.tabs(["Data", "Power", "Frequentist", "Peeking", "Bayesian"])

with data_tab:
    st.subheader("Experiment snapshot")
    metrics = st.columns(4)
    metrics[0].metric("Visitors", f"{len(data):,}")
    metrics[1].metric("Control funded rate", f"{frequentist['control_rate']:.2%}")
    metrics[2].metric("Treatment funded rate", f"{frequentist['treatment_rate']:.2%}")
    metrics[3].metric("Observed lift", f"{frequentist['relative_lift']:.1%}")
    summary = data.groupby("group").agg(
        visitors=("user_id", "count"),
        funded=("converted", "sum"),
        deposits=("initial_deposit", "sum"),
        fraud_accounts=("fraud_flag", "sum"),
        net_revenue=("revenue", "sum"),
    )
    summary["funded_rate"] = summary["funded"] / summary["visitors"]
    summary["fraud_per_funded"] = summary["fraud_accounts"] / summary["funded"].clip(lower=1)
    summary["net_revenue_per_visitor"] = summary["net_revenue"] / summary["visitors"]
    st.dataframe(
        summary.style.format({
            "deposits": "${:,.0f}",
            "net_revenue": "${:,.0f}",
            "funded_rate": "{:.2%}",
            "fraud_per_funded": "{:.2%}",
            "net_revenue_per_visitor": "${:.3f}",
        }),
        use_container_width=True,
    )
    steps = {"Visited": "user_id", "Started application": "started_application", "Passed KYC": "kyc_passed", "Linked bank": "bank_linked", "Funded": "converted"}
    funnel = [
        {"step": step, "group": group, "visitors": int(frame[column].astype(bool).sum())}
        for group, frame in data.groupby("group")
        for step, column in steps.items()
    ]
    chart_cols = st.columns(2)
    funnel_fig = px.funnel(funnel, x="visitors", y="step", color="group", title="Sign-up funnel (treatment acts on the bank-linking step)")
    chart_cols[0].plotly_chart(funnel_fig, use_container_width=True)
    deposits = data[data.converted & ~data.fraud_flag]
    deposit_fig = px.histogram(deposits, x="initial_deposit", color="group", nbins=60, log_x=True, barmode="overlay", opacity=0.6, title="First deposit size (log scale): a few whales drive revenue")
    chart_cols[1].plotly_chart(deposit_fig, use_container_width=True)
    daily = data.groupby(["day", "group"], as_index=False).agg(funded_rate=("converted", "mean"), weekday=("weekday", "first"))
    daily_fig = px.line(daily, x="day", y="funded_rate", color="group", markers=True, hover_data=["weekday"], title="Daily funded-account rate (Friday paydays up, weekends down)")
    st.plotly_chart(daily_fig, use_container_width=True)
    with st.expander("Raw visitor-level data"):
        st.dataframe(data.head(500), use_container_width=True)

with power_tab:
    st.subheader("Power planning")
    st.info(f"Analytic sample size: {analytic_sample_size(baseline_cr, relative_lift):,} users per arm")
    sizes = list(range(max(100, n_users // 10), max(1_000, n_users * 2), max(100, n_users // 10)))
    curve = mde_curve(sizes, baseline_cr)
    st.plotly_chart(px.line(curve, x="sample_size", y="mde", markers=True, labels={"mde": "Detectable relative lift"}, title="MDE curve"), use_container_width=True)
    power = power_curve(sizes[:: max(1, len(sizes) // 8)], baseline_cr, relative_lift, simulations=100, seed=seed)
    fig = go.Figure()
    fig.add_scatter(x=power.sample_size, y=power.analytic_power, mode="lines+markers", name="Analytic")
    fig.add_scatter(x=power.sample_size, y=power.simulated_power, mode="markers", name="Simulated")
    fig.update_layout(title="Analytic vs simulated power", xaxis_title="Users per arm", yaxis_title="Power")
    st.plotly_chart(fig, use_container_width=True)

with frequentist_tab:
    st.subheader("Frequentist analysis")
    if srm["srm_detected"]:
        st.error(f"SRM detected: allocation p-value is {srm['p_value']:.4g}. Investigate before trusting results.")
        by_device = data.groupby(["device", "group"]).size().unstack(fill_value=0)
        by_device["treatment_share"] = by_device["treatment"] / by_device.sum(axis=1)
        st.caption("Allocation by device: the segment far from 50% points to where treatment visitors are being lost.")
        st.dataframe(by_device.style.format({"treatment_share": "{:.1%}"}), use_container_width=True)
    else:
        st.success(f"SRM check passes (p = {srm['p_value']:.3f}).")

    st.markdown("**Primary and value metrics**")
    result_cols = st.columns(3)
    result_cols[0].metric("Funded-account p-value", f"{frequentist['p_value']:.4f}")
    revenue = revenue_ttest(data)
    result_cols[1].metric("Net revenue/visitor p-value", f"{revenue['p_value']:.4f}")
    result_cols[2].metric("Net revenue/visitor difference", f"${revenue['difference']:.3f}")
    revenue_ci = bootstrap_revenue_ci(data, n_boot=1_000, seed=seed)
    st.write(f"Bootstrap 95% CI for net revenue per visitor: **${revenue_ci['ci_low']:.3f} to ${revenue_ci['ci_high']:.3f}**")

    st.markdown("**Guardrail: first-party fraud**")
    fraud = conversion_ztest(data, metric="fraud_flag")
    guard_cols = st.columns(3)
    guard_cols[0].metric("Control fraud per 10k visitors", f"{fraud['control_rate'] * 10_000:.1f}")
    guard_cols[1].metric("Treatment fraud per 10k visitors", f"{fraud['treatment_rate'] * 10_000:.1f}")
    guard_cols[2].metric("Fraud p-value", f"{fraud['p_value']:.4f}")
    st.caption(
        "Fraud is tested per visitor, not per funded account: conditioning on funding (a post-treatment outcome) "
        "would bias the comparison. Fraud is rare, so this guardrail is usually underpowered. "
        "A non-significant result does not show that fraud stayed flat."
    )

    st.markdown("**Segment lifts in funded accounts**")
    segments = []
    for column in ["device", "channel", "customer_type"]:
        for value, frame in data.groupby(column):
            test = conversion_ztest(frame)
            segments.append({"segment": f"{column}: {value}", "visitors": len(frame), "lift": test["relative_lift"], "p_value": test["p_value"]})
    correction = benjamini_hochberg([row["p_value"] for row in segments])
    for row, adjusted in zip(segments, correction["adjusted_p_values"]):
        row["bh_adjusted_p"] = adjusted
    st.caption("With 10 segment cuts, some will look significant by chance. Benjamini-Hochberg adjusts for that.")
    st.dataframe(
        pd.DataFrame(segments).style.format({"lift": "{:.1%}", "p_value": "{:.4f}", "bh_adjusted_p": "{:.4f}"}),
        use_container_width=True,
    )

with peeking_tab:
    st.subheader("The cost of peeking")
    st.caption("These A/A tests have no true effect. Repeated uncorrected looks turn random noise into false wins.")
    raw = sequential_aa_simulation(n_users=min(n_users, 2_000), n_days=n_days, simulations=200, seed=seed)
    fixed = sequential_aa_simulation(n_users=min(n_users, 2_000), n_days=n_days, simulations=200, seed=seed, correction="bonferroni")
    cols = st.columns(2)
    cols[0].metric("Uncorrected false-positive rate", f"{raw['false_positive_rate']:.1%}")
    cols[1].metric("Bonferroni false-positive rate", f"{fixed['false_positive_rate']:.1%}")
    trajectories = raw["trajectories"]
    fig = px.line(trajectories, x="day", y="p_value", color="simulation", title="P-value trajectories for 50 A/A tests")
    fig.add_hline(y=0.05, line_dash="dash", line_color="red", annotation_text="0.05")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(alpha_spending_boundary(n_days), use_container_width=True)

with bayesian_tab:
    st.subheader("Bayesian conversion model")
    posterior = beta_binomial(data, seed=seed)
    cols = st.columns(3)
    cols[0].metric("P(treatment > control)", f"{posterior['prob_treatment_better']:.1%}")
    cols[1].metric("Expected loss", f"{posterior['expected_loss']:.4f}")
    cols[2].metric("Lift credible interval", f"{posterior['lift_ci'][0]:.1%} to {posterior['lift_ci'][1]:.1%}")
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=posterior["control_draws"], histnorm="probability density", name="Control", opacity=0.6))
    fig.add_trace(go.Histogram(x=posterior["treatment_draws"], histnorm="probability density", name="Treatment", opacity=0.6))
    fig.update_layout(barmode="overlay", title="Posterior funded-account rate distributions", xaxis_title="Funded-account rate")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(bayesian_comparison(data, frequentist, seed=seed).style.format({"estimate": "{:.2%}", "lower": "{:.2%}", "upper": "{:.2%}", "evidence": "{:.2%}"}), use_container_width=True)
