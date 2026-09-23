"""Power and sample-size calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


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


def simulate_power(n_per_arm: int, baseline_cr: float, relative_lift: float, simulations: int = 1_000, seed: int = 42, alpha: float = 0.05) -> float:
    """Estimate power by simulating many experiments and z-testing each one."""
    # Visitors are independent, so each arm's funded count is exactly binomial;
    # drawing counts directly matches generating every visitor, far faster.
    rng = np.random.default_rng(seed)
    control = rng.binomial(n_per_arm, baseline_cr, simulations)
    treatment = rng.binomial(n_per_arm, min(baseline_cr * (1 + relative_lift), 1.0), simulations)
    pooled = (control + treatment) / (2 * n_per_arm)
    standard_error = np.sqrt(pooled * (1 - pooled) * 2 / n_per_arm)
    with np.errstate(divide="ignore", invalid="ignore"):
        z_stat = np.nan_to_num((treatment - control) / n_per_arm / standard_error)
    return float(np.mean(2 * norm.sf(np.abs(z_stat)) < alpha))


def planned_power(n_per_arm: int, baseline_cr: float, mde: float, alpha: float = 0.05) -> float:
    """Power to detect a pre-specified relative lift at the current sample size.

    Deliberately not "observed power", which is just a restatement of the p-value.
    """
    effect = proportion_effectsize(baseline_cr * (1 + mde), baseline_cr)
    return float(NormalIndPower().power(abs(effect), nobs1=max(n_per_arm, 1), alpha=alpha, ratio=1))


def days_to_target_power(n_per_arm: int, visitors_per_day: float, baseline_cr: float, mde: float, power: float = 0.8) -> int:
    """Additional days of traffic (split across both arms) needed to reach target power."""
    shortfall = max(0, analytic_sample_size(baseline_cr, mde, power=power) - n_per_arm)
    return int(np.ceil(2 * shortfall / visitors_per_day)) if shortfall else 0


def power_curve(sample_sizes: list[int] | np.ndarray, baseline_cr: float, relative_lift: float, simulations: int = 250, seed: int = 42) -> pd.DataFrame:
    """Return analytic and simulated power across sample sizes."""
    rows = []
    for n in sample_sizes:
        effect = proportion_effectsize(baseline_cr * (1 + relative_lift), baseline_cr)
        analytic = NormalIndPower().power(abs(effect), nobs1=int(n), alpha=0.05, ratio=1)
        rows.append({"sample_size": int(n), "analytic_power": float(analytic), "simulated_power": simulate_power(int(n), baseline_cr, relative_lift, simulations, seed + int(n))})
    return pd.DataFrame(rows)
