"""Synthetic experiment data generation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_experiment(
    n_users: int = 20_000,
    split: float = 0.5,
    baseline_cr: float = 0.04,
    relative_lift: float = 0.05,
    n_days: int = 14,
    seed: int = 42,
    novelty_effect: bool = False,
    srm_injection: float = 0.0,
) -> pd.DataFrame:
    """Generate user-level conversion and revenue data for an A/B test.

    ``split`` is the treatment allocation. ``srm_injection`` removes that
    fraction of treatment users after randomization to make SRM detectable.
    """
    if not 0 < split < 1:
        raise ValueError("split must be between 0 and 1")
    if n_users < 2 or n_days < 1:
        raise ValueError("n_users must be at least 2 and n_days at least 1")
    if not 0 <= srm_injection < 1:
        raise ValueError("srm_injection must be between 0 and 1")

    rng = np.random.default_rng(seed)
    group = np.where(rng.random(n_users) < split, "treatment", "control")
    day = rng.integers(1, n_days + 1, size=n_users)
    device = rng.choice(["mobile", "desktop"], size=n_users, p=[0.65, 0.35])
    user_type = rng.choice(["new", "returning"], size=n_users, p=[0.7, 0.3])

    segment_multiplier = np.where(device == "mobile", 0.90, 1.10)
    segment_multiplier *= np.where(user_type == "new", 0.90, 1.10)
    lift = relative_lift * np.exp(-0.12 * (day - 1)) if novelty_effect else relative_lift
    treatment_rate = baseline_cr * (1 + lift)
    rates = np.where(group == "treatment", treatment_rate, baseline_cr)
    rates = np.clip(rates * segment_multiplier, 0, 1)
    converted = rng.random(n_users) < rates
    revenue = np.where(converted, rng.lognormal(mean=3.5, sigma=0.8, size=n_users), 0.0)

    frame = pd.DataFrame(
        {
            "user_id": np.arange(1, n_users + 1),
            "day": day,
            "group": group,
            "device": device,
            "user_type": user_type,
            "converted": converted,
            "revenue": revenue,
        }
    )
    if srm_injection:
        treatment = frame.index[frame["group"].eq("treatment")]
        remove_count = int(len(treatment) * srm_injection)
        if remove_count:
            frame = frame.drop(rng.choice(treatment, size=remove_count, replace=False))
    return frame.reset_index(drop=True)
