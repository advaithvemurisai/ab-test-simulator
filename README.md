# LiftLab

A product-style experimentation workspace for deciding whether a neobank should ship instant bank linking. LiftLab pairs a funded-account lift with net revenue, fraud guardrails, traffic validity, and the statistical evidence behind each recommendation.

**Live app:** deploy this repository to [Streamlit Community Cloud](https://share.streamlit.io/) and set the entrypoint to `app/streamlit_app.py`.

The default **Growth vs. fraud** scenario is designed for a 30-second portfolio read: a promising conversion result can still fail when the fraud guardrail moves in the wrong direction. The sidebar also includes clear winner, underpowered, broken rollout, and novelty-effect scenarios.

## Scenario

A neobank tests **instant bank linking** (open-banking login) against **micro-deposit verification** in its high-yield savings sign-up flow. Each synthetic row is a randomized visitor:

| Field | What it models |
| --- | --- |
| `started_application` → `kyc_passed` → `bank_linked` → `converted` | Sign-up funnel. The treatment acts on the bank-linking step; `converted` means a funded account |
| `initial_deposit` | Log-normal first deposit, capped at the $250k FDIC insurance limit. Medians vary by channel (affiliate rate-shoppers bring the biggest balances) |
| `revenue` | 90-day net revenue: 1.5% net interest margin on the balance, minus the loss when an account turns out to be fraud |
| `fraud_flag` | First-party fraud (returned deposits). It rises with faster linking and is highest on paid social |
| `device`, `channel`, `customer_type`, `weekday` | Segments. The effect is largest on iOS and weakest on web; Friday paydays lift conversion and weekends bring lower-intent traffic |

SRM injection drops treatment visitors mostly on Android, which mimics a broken app release, so the app can show how a per-segment allocation table points to the root cause.

## Key findings

- A 5% relative lift from a 4% baseline needs a large sample, so underpowered tests produce noisy decisions.
- Revenue per visitor is extremely skewed (most visitors are $0, a few depositors are whales); bootstrap intervals are a useful companion to Welch's t-test.
- A conversion win can be a value loss: extra fraud from instant linking eats a large share of the revenue gain from more funded accounts. Fraud is rare, so the guardrail test is badly underpowered.
- Ten segment cuts produce chance "wins"; Benjamini-Hochberg adjustment separates real heterogeneity from noise.
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

The app is organized around product questions: **Overview**, **Customer journey**, **Segments**, **Test planning**, **Pitfalls lab**, **Bayesian view**, and **Case study**. The notebook at `notebooks/walkthrough.ipynb` remains a compact methods walkthrough.

## Methods

The synthetic generator models randomization, device/channel/customer segments, weekday traffic, funnel progression, lognormal deposits, fraud losses, novelty decay, and SRM injection. The analysis layer includes two-proportion z-tests, Welch's t-test, bootstrap intervals, chi-square SRM checks, Benjamini-Hochberg adjustment, analytic and simulated power, sequential A/A tests, and a Beta-Binomial posterior.
