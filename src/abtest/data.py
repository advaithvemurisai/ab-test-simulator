"""Synthetic fintech experiment data.

Scenario: a neobank tests *instant bank linking* (open-banking login) against the
existing micro-deposit verification step in its high-yield savings sign-up flow.
Each row is a visitor randomized on the savings product page. The primary metric
is a funded account; the value metric is 90-day net revenue (net interest margin
on balances minus fraud losses); the guardrail is first-party fraud (returned
deposits), which faster linking tends to increase.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
# Friday is payday for many users; weekends bring less, lower-intent traffic.
WEEKDAY_TRAFFIC = np.array([1.0, 1.0, 1.0, 1.0, 1.05, 0.7, 0.7])
WEEKDAY_CONVERSION = np.array([1.0, 1.0, 1.0, 1.0, 1.15, 0.85, 0.85])

DEVICES = {
    # share, conversion multiplier, treatment-effect multiplier
    "ios": (0.45, 1.10, 1.25),
    "android": (0.30, 0.90, 1.10),
    "web": (0.25, 0.95, 0.55),
}
CHANNELS = {
    # share, conversion multiplier, median first deposit ($), fraud multiplier
    "organic": (0.35, 1.00, 1_500, 1.0),
    "paid_search": (0.25, 0.90, 2_000, 1.0),
    "paid_social": (0.20, 0.55, 600, 2.5),
    "referral": (0.12, 1.60, 1_800, 0.7),
    "affiliate": (0.08, 1.30, 5_000, 1.5),
}
CUSTOMER_TYPES = {
    # share, conversion multiplier, KYC pass rate, deposit multiplier
    "new_to_bank": (0.75, 0.85, 0.82, 1.0),
    "existing_customer": (0.25, 1.45, 0.99, 1.5),
}

FUND_GIVEN_LINK = 0.70
CONTROL_LINK_RATE = 0.55
NET_INTEREST_MARGIN = 0.015
REVENUE_WINDOW_DAYS = 90
FDIC_LIMIT = 250_000
BASE_FRAUD_RATE = 0.008


def _pick(rng: np.random.Generator, table: dict, n: int) -> np.ndarray:
    names = list(table)
    shares = np.array([table[name][0] for name in names])
    return rng.choice(names, size=n, p=shares / shares.sum())


def _lookup(values: np.ndarray, table: dict, index: int) -> np.ndarray:
    return np.array([table[value][index] for value in values], dtype=float)


def generate_experiment(
    n_users: int = 20_000,
    split: float = 0.5,
    baseline_cr: float = 0.04,
    relative_lift: float = 0.05,
    n_days: int = 14,
    seed: int = 42,
    novelty_effect: bool = False,
    srm_injection: float = 0.0,
    fraud_uplift: float = 0.30,
) -> pd.DataFrame:
    """Generate visitor-level funnel, deposit, fraud, and revenue data.

    ``baseline_cr`` is the control visitor-to-funded-account rate and
    ``relative_lift`` the average treatment effect on it; both are averages over
    the segment mix, so segment rates vary around them. ``fraud_uplift`` is the
    relative increase in fraud among treatment-funded accounts. ``srm_injection``
    drops that fraction of treatment visitors after randomization, concentrated
    on Android (like a broken app release), to make SRM detectable.
    """
    if not 0 < split < 1:
        raise ValueError("split must be between 0 and 1")
    if n_users < 2 or n_days < 1:
        raise ValueError("n_users must be at least 2 and n_days at least 1")
    if not 0 <= srm_injection < 1:
        raise ValueError("srm_injection must be between 0 and 1")
    if fraud_uplift < -1:
        raise ValueError("fraud_uplift must be at least -1")

    rng = np.random.default_rng(seed)
    group = np.where(rng.random(n_users) < split, "treatment", "control")
    is_treatment = group == "treatment"

    day_traffic = WEEKDAY_TRAFFIC[np.arange(n_days) % 7]
    day = rng.choice(np.arange(1, n_days + 1), size=n_users, p=day_traffic / day_traffic.sum())
    weekday_index = (day - 1) % 7
    device = _pick(rng, DEVICES, n_users)
    channel = _pick(rng, CHANNELS, n_users)
    customer_type = _pick(rng, CUSTOMER_TYPES, n_users)

    propensity = (
        WEEKDAY_CONVERSION[weekday_index]
        * _lookup(device, DEVICES, 1)
        * _lookup(channel, CHANNELS, 1)
        * _lookup(customer_type, CUSTOMER_TYPES, 1)
    )
    control_rate = baseline_cr * propensity / propensity.mean()

    effect_weight = _lookup(device, DEVICES, 2)
    user_lift = relative_lift * effect_weight / effect_weight.mean()
    if novelty_effect:
        user_lift = user_lift * np.exp(-0.12 * (day - 1))

    kyc_rate = _lookup(customer_type, CUSTOMER_TYPES, 2)
    start_rate = np.clip(control_rate / (kyc_rate * CONTROL_LINK_RATE * FUND_GIVEN_LINK), 0, 1)
    link_rate = np.clip(CONTROL_LINK_RATE * np.where(is_treatment, 1 + user_lift, 1.0), 0, 1)

    started = rng.random(n_users) < start_rate
    kyc_passed = started & (rng.random(n_users) < kyc_rate)
    bank_linked = kyc_passed & (rng.random(n_users) < link_rate)
    converted = bank_linked & (rng.random(n_users) < FUND_GIVEN_LINK)

    median_deposit = _lookup(channel, CHANNELS, 2) * _lookup(customer_type, CUSTOMER_TYPES, 3)
    deposit = np.clip(rng.lognormal(np.log(median_deposit), 1.3), 10, FDIC_LIMIT).round(2)
    initial_deposit = np.where(converted, deposit, 0.0)

    fraud_rate = BASE_FRAUD_RATE * _lookup(channel, CHANNELS, 3)
    fraud_rate = np.clip(fraud_rate * np.where(is_treatment, 1 + fraud_uplift, 1.0), 0, 1)
    fraud_flag = converted & (rng.random(n_users) < fraud_rate)
    fraud_loss = np.where(fraud_flag, rng.lognormal(np.log(250), 0.9, n_users), 0.0)

    # Balances drift after funding: some users top up, some move money out.
    average_balance = initial_deposit * rng.lognormal(0.05, 0.5, n_users)
    average_balance = np.where(rng.random(n_users) < 0.12, average_balance * 0.2, average_balance)
    interest_revenue = average_balance * NET_INTEREST_MARGIN * REVENUE_WINDOW_DAYS / 365
    revenue = np.where(fraud_flag, -fraud_loss, interest_revenue).round(2)

    frame = pd.DataFrame(
        {
            "user_id": np.arange(1, n_users + 1),
            "day": day,
            "weekday": np.array(WEEKDAYS)[weekday_index],
            "group": group,
            "device": device,
            "channel": channel,
            "customer_type": customer_type,
            "started_application": started,
            "kyc_passed": kyc_passed,
            "bank_linked": bank_linked,
            "converted": converted,
            "initial_deposit": initial_deposit,
            "fraud_flag": fraud_flag,
            "revenue": revenue,
        }
    )
    if srm_injection:
        treatment = frame.index[is_treatment]
        remove_count = int(len(treatment) * srm_injection)
        if remove_count:
            weights = np.where(frame.loc[treatment, "device"].eq("android"), 6.0, 1.0)
            dropped = rng.choice(treatment, size=remove_count, replace=False, p=weights / weights.sum())
            frame = frame.drop(dropped)
    return frame.reset_index(drop=True)
