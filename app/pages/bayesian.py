"""Bayesian evidence page."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from abtest.bayesian import bayesian_comparison, beta_binomial
from abtest.frequentist import conversion_ztest
from app.ui.context import get_context
from app.ui.theme import CONTROL, TREATMENT, chart_theme, explain, inject_theme

inject_theme()
data, _ = get_context()
st.markdown('<div class="eyebrow">Bayesian view</div>', unsafe_allow_html=True)
st.title("How probable is a better treatment?")
st.write("The Beta-Binomial model gives a direct probability statement, while expected loss asks how much conversion rate we give up if treatment is actually worse.")
posterior = beta_binomial(data, seed=42)
cols = st.columns(3)
cols[0].metric("Posterior probability", f"{posterior['prob_treatment_better']:.1%}", "chance treatment is better")
cols[1].metric("Expected loss", f"{posterior['expected_loss']:.4f}", "if treatment is worse")
cols[2].metric("95% credible interval", f"{posterior['lift_ci'][0]:.1%} to {posterior['lift_ci'][1]:.1%}", "relative lift")
fig = go.Figure()
fig.add_trace(go.Histogram(x=posterior["control_draws"], histnorm="probability density", name="Control (micro-deposits)", opacity=.6, marker_color=CONTROL))
fig.add_trace(go.Histogram(x=posterior["treatment_draws"], histnorm="probability density", name="Treatment (instant linking)", opacity=.6, marker_color=TREATMENT))
fig.update_layout(barmode="overlay", title="Posterior funded-account rates overlap where uncertainty remains", xaxis_title="Funded-account rate")
st.plotly_chart(chart_theme(fig), width="stretch")
st.dataframe(bayesian_comparison(data, conversion_ztest(data), seed=42).style.format({"estimate": "{:.2%}", "lower": "{:.2%}", "upper": "{:.2%}", "evidence": "{:.2%}"}), width="stretch")
explain("Posterior probability", "Bayesian: the probability that the new flow is better after updating the prior with observed data.", "Independent Beta(1, 1) priors updated with conversion successes and failures.")
st.warning("Bayesian methods are not a free pass: stopping whenever probability exceeds 95% can also inflate false positives under repeated peeking.")
