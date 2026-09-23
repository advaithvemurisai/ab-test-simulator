"""Shared LiftLab visual system and explanatory copy."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

CONTROL = "#667085"
TREATMENT = "#087f8c"
SUCCESS = "#16845b"
WARNING = "#b7791f"
DANGER = "#c94b4b"


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        :root { --ink:#18252b; --muted:#63727a; --teal:#087f8c; --line:#dbe4e6; --wash:#f4f8f8; }
        html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
        h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0; }
        [data-testid="stSidebar"] { border-right: 1px solid var(--line); }
        .eyebrow { color: var(--teal); font-size:.75rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
        .hero-copy { max-width: 760px; padding: 1.4rem 0 .8rem; }
        .hero-copy h1 { font-size: clamp(2rem, 4vw, 3.8rem); line-height:1.05; margin:.3rem 0 .8rem; }
        .hero-copy p { color:var(--muted); font-size:1.08rem; line-height:1.6; }
        .verdict { border-left: 5px solid var(--teal); background:var(--wash); padding:1.2rem 1.35rem; border-radius:8px; margin:1rem 0 1.4rem; }
        .verdict h2 { margin:0 0 .55rem; }
        .verdict p { color:var(--muted); margin:.25rem 0; }
        .skill-strip { display:flex; flex-wrap:wrap; gap:.45rem; margin:1.1rem 0 1.5rem; }
        .skill { border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:.82rem; padding:.35rem .7rem; }
        .definition { color:var(--muted); font-size:.9rem; line-height:1.5; }
        .how { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:.8rem; margin:.4rem 0 1rem; }
        .step { border:1px solid var(--line); border-radius:8px; padding:.9rem 1rem; display:flex; flex-direction:column; gap:.3rem; }
        .step b { color:var(--ink); }
        .step span:last-child { color:var(--muted); font-size:.9rem; line-height:1.5; }
        .step .num { width:1.6rem; height:1.6rem; border-radius:50%; background:var(--teal); color:#fff; font-size:.8rem; font-weight:700; display:flex; align-items:center; justify-content:center; }
        .verdict-key { display:flex; flex-wrap:wrap; gap:.5rem 1.2rem; color:var(--muted); font-size:.88rem; margin:.2rem 0 .8rem; }
        .chip { display:inline-block; border-radius:4px; padding:.1rem .45rem; margin-right:.4rem; font-size:.72rem; font-weight:700; letter-spacing:.04em; color:#fff; }
        .chip.ship { background:#16845b; } .chip.dont { background:#c94b4b; } .chip.keep { background:#b7791f; } .chip.trust { background:#475467; }
        .catch { color:var(--ink); font-size:.95rem; border-left:3px solid var(--line); padding-left:.8rem; margin:.4rem 0 1rem; }
        @media (max-width: 640px) { .hero-copy h1 { font-size:2.2rem; } .hero-copy p { font-size:1rem; } .how { grid-template-columns:1fr; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def chart_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font={"family": "DM Sans, sans-serif", "color": "#18252b"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 12, "r": 12, "t": 52, "b": 12},
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#e7eeee", zeroline=False)
    return fig


def explain(term: str, meaning: str, detail: str) -> None:
    st.markdown(f"**{term}**  \n<span class='definition'>{meaning}</span>", unsafe_allow_html=True)
    with st.expander("How this is calculated"):
        st.caption(detail)
