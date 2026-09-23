# LiftLab

A product-style experimentation workspace for deciding whether a neobank should ship instant bank linking. LiftLab pairs a funded-account lift with net revenue, fraud guardrails, traffic validity, and the statistical evidence behind each recommendation.

**[Open the live app →](https://ab-test-simulator-gbefknskbhqc9fgythgzks.streamlit.app/)**

The default **Growth vs. fraud** scenario is designed for a 30-second portfolio read: a promising conversion result can still fail when the fraud guardrail moves in the wrong direction. The sidebar also includes clear winner, underpowered, broken rollout, and novelty-effect scenarios.

## How LiftLab decides

The Overview page turns the experiment into one of four recommendations. Rules are applied in order, and the first one that fires wins:

| Verdict | When |
| --- | --- |
| **DON'T TRUST** | The traffic split failed the SRM check (chi-square p < 0.001), so no outcome can be trusted |
| **DON'T SHIP** | Funded accounts are significantly lower, the whole 95% CI for net revenue is below zero, or fraud is significantly worse than a +50% tolerance |
| **KEEP TESTING** | The lift is significant but fading (a treatment-by-period interaction test shows the second half of the test is significantly weaker than the first) |
| **SHIP** | Funded accounts are significantly higher and no guardrail is breached. The card states whether revenue is also up or still uncertain |
| **KEEP TESTING** / **DON'T SHIP** | No significant lift: keep testing if power to detect a planned 5% lift is below 80% (with the extra days needed at current traffic); otherwise don't ship, because a lift that large is unlikely |

Each scenario is covered by a test that checks it reaches its intended verdict:

| Scenario | Verdict | Lesson |
| --- | --- | --- |
| Growth vs. fraud | DON'T SHIP | A conversion win is not enough when a guardrail gets worse |
| Clear winner | SHIP | Primary metric up, guardrails intact, revenue honestly reported as uncertain |
| Too small to tell | KEEP TESTING | A non-significant result from an underpowered test is not evidence of no effect |
| Broken rollout | DON'T TRUST | Check the traffic split before reading any metric |
| Shiny-new effect | KEEP TESTING | A launch-week lift can fade, so the overall average overstates the lasting effect |

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
- A novelty effect can make a test look like a clear win. Comparing the lift in the first and second half of the test catches the fade before it ships.
- "Observed power" (power computed from the effect you happened to see) is just a restatement of the p-value. LiftLab reports power for a planned minimum detectable effect instead, and converts the shortfall into extra days of traffic.
- Looking at an A/A test every day can raise the false-positive rate far above 5%. Alpha spending or a fixed analysis plan controls this error.
- Bayesian posterior probability is intuitive, but stopping whenever `P(treatment > control) > 95%` also creates peeking bias.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
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

The synthetic generator models randomization, device/channel/customer segments, weekday traffic, funnel progression, lognormal deposits, fraud losses, novelty decay, and SRM injection. The analysis layer includes two-proportion z-tests, delta-method confidence intervals for relative lift, Welch's t-test, bootstrap intervals, chi-square SRM checks, a treatment-by-period interaction test for fading lifts, Benjamini-Hochberg adjustment, analytic and simulated power, sequential A/A tests, and a Beta-Binomial posterior. The decision rules live in `src/abtest/decision.py` as pure functions with unit tests.
