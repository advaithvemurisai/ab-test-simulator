"""Power and test-duration planning page."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from abtest.power import analytic_sample_size, power_curve
from app.ui.context import get_context
from app.ui.theme import chart_theme, explain, inject_theme

inject_theme()
data, scenario = get_context()
st.markdown('<div class="eyebrow">Test planning</div>', unsafe_allow_html=True)
st.title("How much evidence is enough?")
st.write("Power is the chance a test catches a real effect. MDE is the smallest effect worth detecting. Both depend on traffic, baseline conversion, and how long you run.")
monthly = st.number_input("Monthly traffic available", 10_000, 5_000_000, 500_000, 10_000)
smallest_lift = st.slider("Smallest lift worth detecting", .01, .50, .05, .01, format="%.0f%%")
required = analytic_sample_size(scenario.baseline_cr, smallest_lift)
run_days = required * 2 / (monthly / 30)
cols = st.columns(3)
cols[0].metric("Required users / arm", f"{required:,}")
cols[1].metric("Estimated run time", f"{run_days:.0f} days")
cols[2].metric("Target power", "80%")

sizes = np.linspace(max(500, required // 4), required * 2, 10).astype(int)
curve = power_curve(sizes, scenario.baseline_cr, smallest_lift, simulations=100, seed=42)
fig = go.Figure()
fig.add_scatter(x=curve.sample_size * 2 / (monthly / 30), y=curve.analytic_power, mode="lines+markers", name="Theoretical power")
fig.add_scatter(x=curve.sample_size * 2 / (monthly / 30), y=curve.simulated_power, mode="markers", name="100 simulated tests")
fig.update_layout(title="Theoretical and simulated power converge as evidence grows", xaxis_title="Test duration (days)", yaxis_title="Power", yaxis_tickformat=".0%")
st.plotly_chart(chart_theme(fig), width="stretch")
explain("Statistical power", "The chance this test catches a real lift of the size you care about.", "Normal approximation for a two-sided two-proportion test at alpha = 0.05.")
explain("MDE", "The smallest lift this test can reliably detect at 80% power.", "Solved by inverting the two-proportion power calculation for each sample size.")
