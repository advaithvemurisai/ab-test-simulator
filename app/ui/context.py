"""Shared sidebar state and cached experiment data."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from abtest.data import generate_experiment
from abtest.scenarios import SCENARIOS, Scenario


def _apply_scenario_defaults() -> None:
    scenario = SCENARIOS[st.session_state["scenario_name"]]
    st.session_state["_liftlab_scenario_name"] = scenario.name
    st.session_state["n_users"] = scenario.n_users
    st.session_state["baseline_cr"] = scenario.baseline_cr
    st.session_state["relative_lift_pct"] = round(scenario.relative_lift * 100)
    st.session_state["fraud_uplift_pct"] = round(scenario.fraud_uplift * 100)
    st.session_state["n_days"] = scenario.n_days
    st.session_state["srm_injection_pct"] = round(scenario.srm_injection * 100)


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


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### LiftLab")
        st.caption("Experiment decision workspace")
        if "_liftlab_scenario_name" not in st.session_state:
            st.session_state["_liftlab_scenario_name"] = next(iter(SCENARIOS))
        scenario_name = st.selectbox("Scenario", list(SCENARIOS), key="scenario_name", on_change=_apply_scenario_defaults)
        scenario = SCENARIOS[scenario_name]
        st.info(f"**Try this:** {scenario.prompt}")
        with st.expander("Advanced settings"):
            st.number_input("Visitors randomized", 200, 100_000, scenario.n_users, 500, key="n_users")
            st.slider("Baseline funded-account rate", .005, .20, scenario.baseline_cr, .005, format="%.3f", key="baseline_cr")
            st.slider("True lift", -50, 100, round(scenario.relative_lift * 100), 1, format="%d%%", key="relative_lift_pct")
            st.slider("Fraud increase", 0, 200, round(scenario.fraud_uplift * 100), 5, format="%d%%", key="fraud_uplift_pct")
            st.slider("Experiment days", 3, 30, scenario.n_days, key="n_days")
            st.slider("Treatment traffic lost", 0, 30, round(scenario.srm_injection * 100), 1, format="%d%%", key="srm_injection_pct")
        st.caption("Seed fixed at 42 so the portfolio demo is reproducible.")


def get_context() -> tuple[object, Scenario]:
    """Read the shell-owned controls and return one shared experiment context."""
    scenario = SCENARIOS[st.session_state.get("_liftlab_scenario_name", next(iter(SCENARIOS)))]
    relative_lift = st.session_state.get("relative_lift_pct", round(scenario.relative_lift * 100)) / 100
    fraud_uplift = st.session_state.get("fraud_uplift_pct", round(scenario.fraud_uplift * 100)) / 100
    srm_injection = st.session_state.get("srm_injection_pct", round(scenario.srm_injection * 100)) / 100
    scenario = replace(
        scenario,
        n_users=int(st.session_state.get("n_users", scenario.n_users)),
        baseline_cr=float(st.session_state.get("baseline_cr", scenario.baseline_cr)),
        relative_lift=relative_lift,
        fraud_uplift=fraud_uplift,
        n_days=int(st.session_state.get("n_days", scenario.n_days)),
        srm_injection=srm_injection,
    )
    data = load_experiment(
        scenario.n_users,
        scenario.baseline_cr,
        scenario.relative_lift,
        scenario.fraud_uplift,
        scenario.n_days,
        scenario.novelty_effect,
        scenario.srm_injection,
    )
    return data, scenario
