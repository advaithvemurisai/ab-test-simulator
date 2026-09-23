"""Shared sidebar state and cached experiment data."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from abtest.data import generate_experiment
from abtest.scenarios import SCENARIOS, Scenario


@st.cache_data(show_spinner=False)
def load_experiment(
    n_users: int,
    baseline_cr: float,
    relative_lift: float,
    fraud_uplift: float,
    n_days: int,
    novelty_effect: bool,
    srm_injection: float,
    seed: int = 42,
):
    return generate_experiment(
        n_users=n_users,
        baseline_cr=baseline_cr,
        relative_lift=relative_lift,
        fraud_uplift=fraud_uplift,
        n_days=n_days,
        novelty_effect=novelty_effect,
        srm_injection=srm_injection,
        seed=seed,
    )


def get_context() -> tuple[object, Scenario]:
    with st.sidebar:
        st.markdown("### LiftLab")
        st.caption("Experiment decision workspace")
        scenario_name = st.selectbox("Scenario", list(SCENARIOS), index=0)
        scenario = SCENARIOS[scenario_name]
        st.info(f"**Try this:** {scenario.prompt}")
        with st.expander("Advanced settings"):
            n_users = st.number_input("Visitors randomized", 200, 100_000, scenario.n_users, 500)
            baseline_cr = st.slider("Baseline funded-account rate", .005, .20, scenario.baseline_cr, .005, format="%.3f")
            relative_lift = st.slider("True lift", -.50, 1.00, scenario.relative_lift, .01, format="%.0f%%")
            fraud_uplift = st.slider("Fraud increase", 0.0, 2.0, scenario.fraud_uplift, .05, format="%.0f%%")
            n_days = st.slider("Experiment days", 3, 30, scenario.n_days)
            srm_injection = st.slider("Treatment traffic lost", 0.0, .30, scenario.srm_injection, .01, format="%.0f%%")
        st.caption("Seed fixed at 42 so the portfolio demo is reproducible.")
    data = load_experiment(int(n_users), baseline_cr, relative_lift, fraud_uplift, n_days, scenario.novelty_effect, srm_injection)
    return data, scenario
