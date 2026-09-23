"""Portfolio-friendly experiment scenario presets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    lesson: str
    n_users: int
    baseline_cr: float
    relative_lift: float
    fraud_uplift: float
    n_days: int
    novelty_effect: bool = False
    srm_injection: float = 0.0
    prompt: str = ""


SCENARIOS = {
    "Growth vs. fraud": Scenario(
        name="Growth vs. fraud",
        description="Instant bank linking promises a faster savings-account signup.",
        lesson="A conversion win is not enough when a guardrail gets worse.",
        n_users=40_000,
        baseline_cr=0.04,
        relative_lift=0.08,
        fraud_uplift=0.80,
        n_days=14,
        prompt="Does the funded-account lift survive the fraud guardrail?",
    ),
    "Clear winner": Scenario(
        name="Clear winner",
        description="A well-tested onboarding change improves funding with little downside.",
        lesson="A clean primary metric, value metric, and guardrail support shipping.",
        n_users=60_000,
        baseline_cr=0.04,
        relative_lift=0.15,
        fraud_uplift=0.05,
        n_days=14,
        prompt="Can you find the evidence for shipping?",
    ),
    "Too small to tell": Scenario(
        name="Too small to tell",
        description="A plausible improvement is tested on a small traffic slice.",
        lesson="A non-significant result is not proof that nothing happened.",
        n_users=5_000,
        baseline_cr=0.04,
        relative_lift=0.05,
        fraud_uplift=0.10,
        n_days=7,
        prompt="Is this a no-effect result, or simply an underpowered test?",
    ),
    "Broken rollout": Scenario(
        name="Broken rollout",
        description="An Android release silently loses treatment visitors.",
        lesson="Validate the traffic split before reading any outcome metric.",
        n_users=40_000,
        baseline_cr=0.04,
        relative_lift=0.08,
        fraud_uplift=0.20,
        n_days=14,
        srm_injection=0.15,
        prompt="Find the allocation problem before trusting the lift.",
    ),
    "Shiny-new effect": Scenario(
        name="Shiny-new effect",
        description="The new flow looks exciting at launch (+60% on day one), then its lift fades.",
        lesson="Novelty can make an early read look better than the durable effect.",
        n_users=100_000,
        baseline_cr=0.04,
        relative_lift=0.60,
        fraud_uplift=0.15,
        n_days=28,
        novelty_effect=True,
        prompt="Compare the first week with the late-period trend.",
    ),
}


def get_scenario(name: str) -> Scenario:
    """Return a named preset or raise a useful error for invalid UI state."""
    try:
        return SCENARIOS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown scenario: {name}") from exc
