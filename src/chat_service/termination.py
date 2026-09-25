from .conditions import evaluate_condition_group
from .models import (
    NegotiationState,
    Scenario,
)


def check_termination(
    scenario: Scenario,
    state: NegotiationState,
) -> str | None:

    if state.outcome is not None:
        return state.outcome

    rules = sorted(
        scenario.termination_rules,
        key=lambda rule: rule.priority,
    )

    for rule in rules:

        if evaluate_condition_group(
            rule.when,
            state,
        ):
            state.outcome = rule.outcome_id
            return rule.outcome_id

    return None


def force_outcome(
    state: NegotiationState,
    outcome: str,
) -> str:

    state.outcome = outcome

    return outcome