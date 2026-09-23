# A/B Test Simulator

A hands-on simulator for understanding power, skewed revenue, sequential testing, SRM, and Bayesian decisions in online experiments.

**Live app:** deploy this repository to [Streamlit Community Cloud](https://share.streamlit.io/) and set the entrypoint to `app/streamlit_app.py`.

## Key findings

- A 5% relative lift from a 4% baseline needs a large sample, so underpowered tests produce noisy decisions.
- Revenue per user is heavily skewed; bootstrap intervals are a useful companion to Welch's t-test.
- Looking at an A/A test every day can raise the false-positive rate far above 5%. Alpha spending or a fixed analysis plan controls this error.
- Bayesian posterior probability is intuitive, but stopping whenever `P(treatment > control) > 95%` also creates peeking bias.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Run the checks:

```bash
pytest
ruff check .
```

The notebook at `notebooks/walkthrough.ipynb` mirrors the app's main analysis flow. For a polished project portfolio, capture screenshots or GIFs of the power curve, segment lift table, and especially the peeking chart after launching the app.
