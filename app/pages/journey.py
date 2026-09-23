"""Customer journey and value distribution page."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))
from app.ui.context import get_context
from app.ui.theme import CONTROL, TREATMENT, chart_theme, inject_theme

inject_theme()
data, scenario = get_context()
st.markdown('<div class="eyebrow">Customer journey</div>', unsafe_allow_html=True)
st.title("Where does the experience change?")
st.write("Instant linking is designed to remove friction between KYC and a funded account. The funnel shows whether the effect appears at that step, rather than somewhere upstream.")
steps = {"Visited": "user_id", "Started application": "started_application", "Passed KYC": "kyc_passed", "Linked bank": "bank_linked", "Funded": "converted"}
funnel = [{"Step": step, "Group": group, "Visitors": int(frame[column].astype(bool).sum())} for group, frame in data.groupby("group") for step, column in steps.items()]
fig = px.funnel(funnel, x="Visitors", y="Step", color="Group", color_discrete_map={"control": CONTROL, "treatment": TREATMENT}, title="Treatment separates at the bank-linking step")
st.plotly_chart(chart_theme(fig), width="stretch")

st.subheader("Deposits are skewed by design")
deposits = data[data.converted & ~data.fraud_flag]
fig = px.histogram(deposits, x="initial_deposit", color="group", nbins=60, log_x=True, barmode="overlay", opacity=.65, color_discrete_map={"control": CONTROL, "treatment": TREATMENT}, title="A few high-balance customers drive a large share of value")
st.plotly_chart(chart_theme(fig), width="stretch")
st.caption("This is why net revenue per visitor gets a bootstrap interval rather than relying on a normal-looking histogram.")

daily = data.groupby(["day", "group"], as_index=False).agg(funded_rate=("converted", "mean"), weekday=("weekday", "first"))
fig = px.line(daily, x="day", y="funded_rate", color="group", markers=True, hover_data=["weekday"], color_discrete_map={"control": CONTROL, "treatment": TREATMENT}, title="Daily funded-account rate: watch for novelty decay")
if scenario.novelty_effect:
    fig.add_annotation(x=int(data.day.max() * .75), y=float(daily.funded_rate.max()), text="Novelty effect fades", showarrow=True, arrowhead=2)
st.plotly_chart(chart_theme(fig), width="stretch")
with st.expander("Raw visitor-level data"):
    st.dataframe(data.head(500), width="stretch")
