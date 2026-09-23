"""LiftLab navigation shell."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from app.ui.context import render_sidebar

st.set_page_config(page_title="LiftLab", page_icon=None, layout="wide", initial_sidebar_state="expanded")
render_sidebar()

pages = {
    "Decision": [
        st.Page("pages/overview.py", title="Overview", default=True),
        st.Page("pages/journey.py", title="Customer journey"),
        st.Page("pages/segments.py", title="Segments"),
    ],
    "Evidence": [
        st.Page("pages/planning.py", title="Test planning"),
        st.Page("pages/pitfalls.py", title="Pitfalls lab"),
        st.Page("pages/bayesian.py", title="Bayesian view"),
    ],
    "Portfolio": [st.Page("pages/case_study.py", title="Case study")],
}

st.navigation(pages).run()
