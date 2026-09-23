from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "app" / "streamlit_app.py"


def test_overview_renders_shared_sidebar_and_verdict():
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert app.sidebar.selectbox[0].value == "Growth vs. fraud"
    assert any("Recommendation" in item.value for item in app.markdown)


@pytest.mark.parametrize(
    ("scenario", "verdict"),
    [
        ("Growth vs. fraud", "DON'T SHIP"),
        ("Clear winner", "SHIP"),
        ("Too small to tell", "KEEP TESTING"),
        ("Broken rollout", "DON'T TRUST"),
        ("Shiny-new effect", "KEEP TESTING"),
    ],
)
def test_each_scenario_reaches_its_intended_verdict(scenario, verdict):
    app = AppTest.from_file(APP).run(timeout=30)
    app.sidebar.selectbox[0].set_value(scenario).run(timeout=30)
    card = next(item.value for item in app.markdown if "Recommendation" in item.value)
    assert f"<h2>{verdict}</h2>" in card


def test_scenario_selection_persists_when_switching_pages():
    app = AppTest.from_file(APP).run(timeout=30)
    app.sidebar.selectbox[0].set_value("Broken rollout").run(timeout=30)
    assert app.sidebar.selectbox[0].value == "Broken rollout"
    app.switch_page("pages/segments.py").run(timeout=30)
    assert not app.exception
    assert app.session_state["_liftlab_scenario_name"] == "Broken rollout"


def test_planning_page_renders_power_simulation_quickly():
    app = AppTest.from_file(APP).run(timeout=30)
    app.switch_page("pages/planning.py").run(timeout=10)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 1
