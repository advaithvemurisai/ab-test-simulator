"""Conjugate Beta-Binomial Bayesian analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd


def beta_binomial(data: pd.DataFrame, draws: int = 50_000, seed: int = 42, prior: tuple[float, float] = (1, 1)) -> dict[str, object]:
    """Sample conversion posteriors and summarize treatment vs control."""
    rng = np.random.default_rng(seed)
    control = data[data.group == "control"]["converted"]
    treatment = data[data.group == "treatment"]["converted"]
    a0, b0 = prior
    control_draws = rng.beta(a0 + control.sum(), b0 + len(control) - control.sum(), draws)
    treatment_draws = rng.beta(a0 + treatment.sum(), b0 + len(treatment) - treatment.sum(), draws)
    lift_draws = treatment_draws / control_draws - 1
    expected_loss = float(np.maximum(control_draws - treatment_draws, 0).mean())
    return {
        "control_draws": control_draws,
        "treatment_draws": treatment_draws,
        "lift_draws": lift_draws,
        "prob_treatment_better": float(np.mean(treatment_draws > control_draws)),
        "expected_loss": expected_loss,
        "control_ci": tuple(np.quantile(control_draws, [0.025, 0.975])),
        "treatment_ci": tuple(np.quantile(treatment_draws, [0.025, 0.975])),
        "lift_ci": tuple(np.quantile(lift_draws, [0.025, 0.975])),
    }


def bayesian_comparison(data: pd.DataFrame, frequentist_result: dict[str, float], seed: int = 42) -> pd.DataFrame:
    """Put frequentist and Bayesian decision summaries in one table."""
    result = beta_binomial(data, seed=seed)
    return pd.DataFrame([
        {"method": "Frequentist", "estimate": frequentist_result["relative_lift"], "lower": np.nan, "upper": np.nan, "evidence": 1 - frequentist_result["p_value"]},
        {"method": "Bayesian", "estimate": float(np.mean(result["lift_draws"])), "lower": result["lift_ci"][0], "upper": result["lift_ci"][1], "evidence": result["prob_treatment_better"]},
    ])


def bayesian_peeking_false_positive_rate(n_users: int = 1_000, n_days: int = 14, simulations: int = 500, threshold: float = 0.95, seed: int = 42) -> float:
    """Estimate false positives from stopping when posterior probability exceeds a threshold."""
    false_positives = 0
    for iteration in range(simulations):
        rng = np.random.default_rng(seed + iteration)
        groups = rng.choice(["control", "treatment"], n_users)
        converted = rng.random(n_users) < 0.04
        data = pd.DataFrame({"group": groups, "converted": converted, "day": rng.integers(1, n_days + 1, n_users)})
        for day in range(1, n_days + 1):
            result = beta_binomial(data[data.day <= day], draws=2_000, seed=seed + iteration + day)
            if result["prob_treatment_better"] > threshold:
                false_positives += 1
                break
    return false_positives / simulations
