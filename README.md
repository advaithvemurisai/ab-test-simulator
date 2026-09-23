# LiftLab

**Should a neobank ship instant bank linking?** LiftLab is an experimentation workspace that answers that question the way a product team would: it weighs the lift in funded accounts against revenue, fraud, and the quality of the test itself, then gives a clear recommendation with the evidence behind it.

**[Open the live app →](https://ab-test-simulator-gbefknskbhqc9fgythgzks.streamlit.app/)**

The default scenario is built for a 30-second read: a conversion win that still shouldn't ship, because fraud gets worse.

## What it decides

Every experiment ends in one of four recommendations: **Ship**, **Don't ship**, **Keep testing**, or **Don't trust** (when the test itself is broken). Five built-in scenarios each teach one lesson:

| Scenario | Verdict | Lesson |
| --- | --- | --- |
| Growth vs. fraud | Don't ship | A conversion win is not enough when a guardrail gets worse |
| Clear winner | Ship | Primary metric up, guardrails intact, revenue honestly reported as uncertain |
| Too small to tell | Keep testing | A non-significant result from an underpowered test is not evidence of no effect |
| Broken rollout | Don't trust | Check the traffic split before reading any metric |
| Shiny-new effect | Keep testing | A launch-week lift can fade, so the overall average overstates the lasting effect |

## Key findings

- **A conversion win can be a value loss.** Extra fraud from faster linking can eat much of the revenue gained from more funded accounts.
- **Small tests mislead.** A realistic lift on a low baseline needs a large sample, and "no significant result" often just means "not enough data yet".
- **Slicing by segment produces false wins** unless you correct for running many comparisons.
- **Checking results every day inflates false positives**, for classic and Bayesian tests alike, unless the analysis plan accounts for it.

## Methods

Synthetic randomized-visitor data with a realistic sign-up funnel, skewed deposits, and fraud losses; significance tests, confidence and bootstrap intervals, traffic-split checks, power analysis, multiple-comparison correction, and a Bayesian view. The decision rules are unit tested against every scenario.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Run the checks with `pytest` and `ruff check .`.
