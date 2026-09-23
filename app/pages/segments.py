"""Segment heterogeneity and multiple-testing page."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from abtest.frequentist import benjamini_hochberg, conversion_ztest
from app.ui.context import get_context
from app.ui.theme import TREATMENT, chart_theme, inject_theme

inject_theme()
data, _ = get_context()
st.markdown('<div class="eyebrow">Segments</div>', unsafe_allow_html=True)
st.title("Who does the new flow work for?")
st.write("Segment cuts are useful for learning, but they multiply the number of chances to see a random win. This view reports the lift and adjusts p-values across all cuts.")
rows = []
for column in ["device", "channel", "customer_type"]:
    for value, frame in data.groupby(column):
        result = conversion_ztest(frame)
        half_width = 1.96 * (max(result["control_rate"] * (1 - result["control_rate"]) / max((frame.group == "control").sum(), 1), 1e-9) + max(result["treatment_rate"] * (1 - result["treatment_rate"]) / max((frame.group == "treatment").sum(), 1), 1e-9)) ** .5
        rows.append({"segment": f"{column}: {value}", "lift": result["relative_lift"], "ci_low": result["relative_lift"] - half_width / max(result["control_rate"], .001), "ci_high": result["relative_lift"] + half_width / max(result["control_rate"], .001), "p_value": result["p_value"]})
correction = benjamini_hochberg([row["p_value"] for row in rows])
for row, adjusted in zip(rows, correction["adjusted_p_values"]):
    row["adjusted_p"] = adjusted
frame = pd.DataFrame(rows).sort_values("lift")
fig = go.Figure()
fig.add_vline(x=0, line_color="#9aa7aa")
for _, row in frame.iterrows():
    fig.add_trace(go.Scatter(x=[row.ci_low, row.ci_high], y=[row.segment, row.segment], mode="lines", line={"color": TREATMENT, "width": 5}, showlegend=False))
    fig.add_trace(go.Scatter(x=[row.lift], y=[row.segment], mode="markers", marker={"color": TREATMENT, "size": 10}, showlegend=False))
fig.update_layout(title="Segment lift with approximate 95% intervals", xaxis_title="Relative lift in funded-account rate", yaxis_title="")
st.plotly_chart(chart_theme(fig), width="stretch")
st.caption("Testing many segments creates false wins by chance, so the adjusted p-value is the one to use for claims.")
st.dataframe(frame[["segment", "lift", "p_value", "adjusted_p"]].style.format({"lift": "{:.1%}", "p_value": "{:.4f}", "adjusted_p": "{:.4f}"}), width="stretch")
