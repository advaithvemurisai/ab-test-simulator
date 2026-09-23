"""Portfolio case study page."""

import streamlit as st

from app.ui.theme import inject_theme

inject_theme()
st.markdown('<div class="eyebrow">Case study</div>', unsafe_allow_html=True)
st.title("Instant bank linking: a decision under uncertainty")
st.markdown("""
### Problem
A neobank wants to reduce signup friction by replacing micro-deposit verification with instant bank linking. The obvious question is whether more visitors fund an account. The harder question is whether the extra funded accounts create durable value after interest margin and first-party fraud.

### Data design
Every synthetic visitor is randomized into control or treatment, then moves through a realistic funnel: application start, KYC, bank linking, funding, deposit balance, and fraud. Device, acquisition channel, customer type, weekday traffic, novelty decay, and skewed deposits create the kinds of heterogeneity and noise that make real experiments interesting.

### Methods
The app combines two-proportion z-tests, Welch's t-test, bootstrap intervals, SRM diagnostics, Benjamini-Hochberg correction, power analysis, sequential A/A simulations, and a conjugate Beta-Binomial model. The decision engine keeps validity and guardrails ahead of a tempting primary-metric win.

### Limitations and next steps
This is synthetic data, so it demonstrates method rather than proving a production effect. A real launch would add CUPED variance reduction, pre-registered stopping rules, longer-term retention, and heterogeneous-effect modelling with uplift methods.
""")
st.link_button("View the source on GitHub", "https://github.com/advaithvemurisai/ab-test-simulator")
