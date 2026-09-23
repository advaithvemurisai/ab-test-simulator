"""Power and sample-size calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from .data import generate_experiment
from .frequentist import conversion_ztest


def analytic_sample_size(baseline_cr: float, relative_lift: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Return required users per arm for a two-sided two-proportion test."""
    treatment_cr = baseline_cr * (1 + relative_lift)
    effect = proportion_effectsize(treatment_cr, baseline_cr)
    size = NormalIndPower().solve_power(effect_size=abs(effect), alpha=alpha, power=power, ratio=1)
    return int(np.ceil(size))


def mde_curve(sample_sizes: list[int] | np.ndarray, baseline_cr: float, alpha: float = 0.05, power: float = 0.8) -> pd.DataFrame:
    """Calculate the relative lift detectable at each per-arm sample size."""
    rows = []
    solver = NormalIndPower()
    for n in sample_sizes:
        effect = solver.solve_power(nobs1=int(n), alpha=alpha, power=power, ratio=1)
        low, high = 1e-8, min(0.999 / baseline_cr - 1, 20.0)
        for _ in range(60):
            midpoint = (low + high) / 2
            if abs(proportion_effectsize(baseline_cr * (1 + midpoint), baseline_cr)) > effect:
                high = midpoint
            else:
                low = midpoint
        rows.append({"sample_size": int(n), "mde": (low + high) / 2})
    return pd.DataFrame(rows)


def simulate_power(n_per_arm: int, baseline_cr: float, relative_lift: float, simulations: int = 1_000, seed: int = 42) -> float:
    """Estimate power by repeatedly generating and testing experiments."""
    significant = 0
    for iteration in range(simulations):
        data = generate_experiment(n_users=n_per_arm * 2, baseline_cr=baseline_cr, relative_lift=relative_lift, seed=seed + iteration)
        significant += conversion_ztest(data)["p_value"] < 0.05
    return float(significant / simulations)


def power_curve(sample_sizes: list[int] | np.ndarray, baseline_cr: float, relative_lift: float, simulations: int = 250, seed: int = 42) -> pd.DataFrame:
    """Return analytic and simulated power across sample sizes."""
    rows = []
    for n in sample_sizes:
        effect = proportion_effectsize(baseline_cr * (1 + relative_lift), baseline_cr)
        analytic = NormalIndPower().power(abs(effect), nobs1=int(n), alpha=0.05, ratio=1)
        rows.append({"sample_size": int(n), "analytic_power": float(analytic), "simulated_power": simulate_power(int(n), baseline_cr, relative_lift, simulations, seed + int(n))})
    return pd.DataFrame(rows)
