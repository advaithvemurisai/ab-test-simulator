"""Frequentist A/B test analyses."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest


def conversion_ztest(data: pd.DataFrame, metric: str = "converted") -> dict[str, float]:
    """Compare treatment and control rates of a binary metric with a two-sided z-test."""
    control = data[data.group == "control"][metric]
    treatment = data[data.group == "treatment"][metric]
    counts = np.array([treatment.sum(), control.sum()])
    sizes = np.array([len(treatment), len(control)])
    z_stat, p_value = proportions_ztest(counts, sizes)
    control_rate, treatment_rate = counts[1] / sizes[1], counts[0] / sizes[0]
    return {
        "control_rate": float(control_rate),
        "treatment_rate": float(treatment_rate),
        "absolute_lift": float(treatment_rate - control_rate),
        "relative_lift": float(treatment_rate / control_rate - 1) if control_rate else np.nan,
        "z_stat": float(z_stat),
        "p_value": float(p_value),
    }


def revenue_ttest(data: pd.DataFrame) -> dict[str, float]:
    """Compare per-user revenue using Welch's unequal-variance t-test."""
    control = data.loc[data.group == "control", "revenue"]
    treatment = data.loc[data.group == "treatment", "revenue"]
    result = stats.ttest_ind(treatment, control, equal_var=False)
    return {
        "control_mean": float(control.mean()),
        "treatment_mean": float(treatment.mean()),
        "difference": float(treatment.mean() - control.mean()),
        "p_value": float(result.pvalue),
    }


def bootstrap_revenue_ci(
    data: pd.DataFrame, n_boot: int = 2_000, confidence: float = 0.95, seed: int = 42
) -> dict[str, float]:
    """Bootstrap the treatment-control mean revenue difference."""
    rng = np.random.default_rng(seed)
    control = data.loc[data.group == "control", "revenue"].to_numpy()
    treatment = data.loc[data.group == "treatment", "revenue"].to_numpy()
    control_samples = rng.choice(control, (n_boot, len(control)), replace=True).mean(axis=1)
    treatment_samples = rng.choice(treatment, (n_boot, len(treatment)), replace=True).mean(axis=1)
    differences = treatment_samples - control_samples
    alpha = (1 - confidence) / 2
    low, high = np.quantile(differences, [alpha, 1 - alpha])
    return {"difference": float(differences.mean()), "ci_low": float(low), "ci_high": float(high)}


def srm_check(data: pd.DataFrame, split: float = 0.5) -> dict[str, float | bool]:
    """Check group allocation against the planned split with chi-square."""
    counts = data["group"].value_counts().reindex(["control", "treatment"], fill_value=0)
    expected = np.array([len(data) * (1 - split), len(data) * split])
    statistic, p_value = stats.chisquare(counts.to_numpy(), expected)
    return {"control_count": int(counts["control"]), "treatment_count": int(counts["treatment"]), "chi2": float(statistic), "p_value": float(p_value), "srm_detected": bool(p_value < 0.001)}


def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> dict[str, object]:
    """Return BH-adjusted p-values and rejection decisions."""
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    adjusted[order] = np.minimum.accumulate((values[order] * len(values) / np.arange(1, len(values) + 1))[::-1])[::-1]
    adjusted = np.clip(adjusted, 0, 1)
    return {"adjusted_p_values": adjusted.tolist(), "reject": (adjusted < alpha).tolist()}
