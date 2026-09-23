"""Pure decision rules for the experiment verdict card."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Verdict:
    label: str
    tone: str
    reasons: tuple[str, ...]
    additional_days: int = 0


def decide(
    *,
    srm_p_value: float,
    funded_lift: float,
    funded_p_value: float,
    revenue_ci_low: float,
    revenue_ci_high: float,
    fraud_relative_lift: float,
    fraud_p_value: float,
    fraud_tolerance: float = 0.50,
    current_power: float = 0.0,
    days_elapsed: int = 14,
) -> Verdict:
    """Apply validity, downside, upside, then uncertainty rules in order."""
    if srm_p_value < 0.001:
        return Verdict("DON'T TRUST", "invalid", ("SRM (sample ratio mismatch): fix the traffic split before interpreting outcomes.",))
    if funded_p_value < 0.05 and funded_lift < 0:
        return Verdict("DON'T SHIP", "danger", ("The funded-account rate is significantly lower in treatment.",))
    if revenue_ci_high < 0:
        return Verdict("DON'T SHIP", "danger", ("The 95% confidence interval for net revenue is entirely below zero.",))
    if fraud_p_value < 0.05 and fraud_relative_lift > fraud_tolerance:
        return Verdict("DON'T SHIP", "danger", ("The fraud guardrail is significantly worse than the preset tolerance.",))
    if funded_p_value < 0.05 and funded_lift > 0 and not (fraud_p_value < 0.05 and fraud_relative_lift > fraud_tolerance):
        return Verdict("SHIP", "success", ("The primary metric is significantly positive.", "Value is not below the tolerated loss floor.", "The fraud guardrail is not breached."))
    missing_power = max(0.0, 0.80 - current_power)
    additional_days = round(days_elapsed * missing_power / max(current_power, 0.05)) if missing_power else 0
    return Verdict("KEEP TESTING", "warning", ("The evidence is not decisive yet.", f"Current statistical power is {current_power:.0%}; more data can separate a small lift from noise."), max(additional_days, 1))
