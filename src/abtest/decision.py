"""Pure decision rules for the experiment verdict card."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Verdict:
    label: str
    tone: str
    reasons: tuple[str, ...]
    additional_days: int = 0


def _money(value: float) -> str:
    return f"-${abs(value):.2f}" if value < 0 else f"${value:.2f}"


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
    early_lift: float | None = None,
    late_lift: float | None = None,
    fade_p_value: float | None = None,
    planned_mde: float = 0.05,
    current_power: float = 0.0,
    additional_days: int = 0,
) -> Verdict:
    """Apply validity, downside, durability, upside, then uncertainty rules in order.

    ``current_power`` is the power to detect ``planned_mde`` at the current sample
    size, not power computed from the observed lift.
    """
    if srm_p_value < 0.001:
        return Verdict("DON'T TRUST", "invalid", ("SRM (sample ratio mismatch): fix the traffic split before interpreting outcomes.",))
    if funded_p_value < 0.05 and funded_lift < 0:
        return Verdict("DON'T SHIP", "danger", ("The funded-account rate is significantly lower in treatment.",))
    if revenue_ci_high < 0:
        return Verdict("DON'T SHIP", "danger", ("The 95% confidence interval for net revenue is entirely below zero.",))
    if fraud_p_value < 0.05 and fraud_relative_lift > fraud_tolerance:
        return Verdict("DON'T SHIP", "danger", (f"Fraud is significantly worse, beyond the +{fraud_tolerance:.0%} tolerance.",))

    if funded_p_value < 0.05 and funded_lift > 0:
        fading = (
            early_lift is not None
            and late_lift is not None
            and fade_p_value is not None
            and fade_p_value < 0.05
            and late_lift < early_lift
        )
        if fading:
            return Verdict(
                "KEEP TESTING",
                "warning",
                (
                    f"The lift is fading: {early_lift:+.0%} in the first half of the test vs {late_lift:+.0%} in the second half (decline p = {fade_p_value:.3f}).",
                    "The overall win may be a novelty effect. Keep running (at least another full week) to measure the lasting effect.",
                ),
                max(additional_days, 7),
            )
        revenue_range = f"95% CI {_money(revenue_ci_low)} to {_money(revenue_ci_high)} per visitor"
        revenue_reason = (
            f"Net revenue is also up ({revenue_range})."
            if revenue_ci_low >= 0
            else f"Net revenue impact is uncertain ({revenue_range}) but not clearly negative."
        )
        return Verdict(
            "SHIP",
            "success",
            (
                "The funded-account rate is significantly higher in treatment.",
                revenue_reason,
                f"Fraud is not significantly above the +{fraud_tolerance:.0%} tolerance.",
            ),
        )

    if current_power >= 0.80:
        return Verdict(
            "DON'T SHIP",
            "danger",
            (
                "No significant lift in funded accounts.",
                f"The test had {current_power:.0%} power to detect a {planned_mde:.0%} lift, so a lift that large is unlikely.",
            ),
        )
    return Verdict(
        "KEEP TESTING",
        "warning",
        (
            "The evidence is not decisive yet.",
            f"Power to detect a {planned_mde:.0%} lift is only {current_power:.0%} (target: 80%), so a real lift could still be hiding in the noise.",
        ),
        max(additional_days, 1),
    )
