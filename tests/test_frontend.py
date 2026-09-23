from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "app" / "streamlit_app.py"


def test_overview_renders_shared_sidebar_and_verdict():
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert app.sidebar.selectbox[0].value == "Growth vs. fraud"
    assert any("Recommendation" in item.value for item in app.markdown)


def test_scenario_selection_persists_when_switching_pages():
    app = AppTest.from_file(APP).run(timeout=30)
    app.sidebar.selectbox[0].set_value("Broken rollout").run(timeout=30)
    assert app.sidebar.selectbox[0].value == "Broken rollout"
    app.switch_page("pages/segments.py").run(timeout=30)
    assert not app.exception
    assert app.session_state["_liftlab_scenario_name"] == "Broken rollout"


def test_planning_page_does_not_run_simulations_until_clicked():
    app = AppTest.from_file(APP).run(timeout=30)
    app.switch_page("pages/planning.py").run(timeout=30)
    assert not app.exception
    assert any("simulation is optional" in item.value for item in app.info)
    assert app.button[0].label.startswith("Run 25 simulated experiments")
