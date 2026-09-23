"""Interactive pitfalls lab."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from abtest.sequential import alpha_spending_boundary, sequential_aa_simulation
from app.ui.context import get_context
from app.ui.theme import DANGER, chart_theme, inject_theme

inject_theme()
data, scenario = get_context()
st.markdown('<div class="eyebrow">Pitfalls lab</div>', unsafe_allow_html=True)
st.title("Where good experiments go wrong")
st.write("Each demo is a reminder that a clean-looking result can still be biased by the way the experiment was run.")

st.subheader("Peeking: repeated looks create false wins")
raw = sequential_aa_simulation(n_users=min(len(data), 2_000), n_days=scenario.n_days, simulations=250, seed=42)
fixed = sequential_aa_simulation(n_users=min(len(data), 2_000), n_days=scenario.n_days, simulations=250, seed=42, correction="bonferroni")
cols = st.columns(2)
cols[0].metric("Uncorrected A/A false positives", f"{raw['false_positive_rate']:.1%}", "daily p < 0.05")
cols[1].metric("Bonferroni false positives", f"{fixed['false_positive_rate']:.1%}", "fixed alpha budget")
fig = px.line(raw["trajectories"], x="day", y="p_value", color="simulation", title="Noise crosses 0.05 when you look every day")
fig.add_hline(y=.05, line_dash="dash", line_color=DANGER)
st.plotly_chart(chart_theme(fig), width="stretch")
st.dataframe(alpha_spending_boundary(scenario.n_days), width="stretch")

st.subheader("Broken split: diagnose before interpreting")
srm = data.groupby(["device", "group"]).size().unstack(fill_value=0)
srm["Treatment share"] = srm["treatment"] / (srm["control"] + srm["treatment"])
st.dataframe(srm.style.format({"Treatment share": "{:.1%}"}), width="stretch")
if scenario.srm_injection:
    st.warning("This scenario intentionally loses treatment traffic. The Android row should make the source visible.")
else:
    st.success("This scenario does not inject an SRM problem.")

st.subheader("Novelty and skew")
cols = st.columns(2)
cols[0].markdown("**Novelty effect**\n\nRun full weeks and compare early versus late lift when excitement fades.")
cols[1].markdown("**Skewed revenue**\n\nUse bootstrap confidence intervals or winsorize extreme deposits before making a value claim.")
