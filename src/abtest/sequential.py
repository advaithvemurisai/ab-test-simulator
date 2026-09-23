"""Sequential testing and peeking simulations."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.proportion import proportions_ztest


def _daily_aa(seed: int, n_users: int, n_days: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"group": rng.choice(["control", "treatment"], n_users), "day": rng.integers(1, n_days + 1, n_users), "converted": rng.random(n_users) < 0.04})


def sequential_aa_simulation(n_users: int = 2_000, n_days: int = 14, simulations: int = 1_000, seed: int = 42, alpha: float = 0.05, correction: str = "none") -> dict[str, object]:
    """Simulate A/A peeking and return false-positive rate plus trajectories."""
    false_positives = 0
    trajectories: list[dict[str, float]] = []
    looks = np.arange(1, n_days + 1)
    spending = alpha / n_days if correction == "bonferroni" else alpha
    for iteration in range(simulations):
        data = _daily_aa(seed + iteration, n_users, n_days)
        stopped = False
        for day in looks:
            current = data[data.day <= day]
            counts = current.groupby("group")["converted"].agg(["sum", "count"]).reindex(["control", "treatment"])
            if counts["count"].min() == 0:
                continue
            _, p_value = proportions_ztest(counts["sum"].to_numpy(), counts["count"].to_numpy())
            if iteration < 50:
                trajectories.append({"simulation": iteration, "day": int(day), "p_value": float(p_value)})
            if p_value < spending and not stopped:
                false_positives += 1
                stopped = True
    return {"false_positive_rate": false_positives / simulations, "trajectories": pd.DataFrame(trajectories), "alpha_boundary": spending}


def alpha_spending_boundary(n_days: int, alpha: float = 0.05) -> pd.DataFrame:
    """Return a conservative O'Brien-Fleming-inspired boundary by look."""
    looks = np.arange(1, n_days + 1)
    information_fraction = looks / n_days
    z_boundary = norm.ppf(1 - alpha / 2) / np.sqrt(information_fraction)
    return pd.DataFrame({"day": looks, "alpha": 2 * (1 - norm.cdf(z_boundary)), "z_boundary": z_boundary})
