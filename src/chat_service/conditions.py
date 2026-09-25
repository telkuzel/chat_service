from typing import Any

from .models import (
    Condition,
    ConditionGroup,
    NegotiationState,
)


def compare(
    actual: Any,
    operator: str,
    expected: Any,
) -> bool:

    if operator == "==":
        return actual == expected

    if operator == "!=":
        return actual != expected

    if operator == ">":
        return actual > expected

    if operator == ">=":
        return actual >= expected

    if operator == "<":
        return actual < expected

    if operator == "<=":
        return actual <= expected

    return False


def evaluate_condition(
    condition: Condition,
    state: NegotiationState,
) -> bool:

    if condition.metric is not None:

        actual = state.metrics.get(
            condition.metric
        )

        if actual is None:
            return False

        return compare(
            actual,
            condition.operator or "==",
            condition.value,
        )

    if condition.fact_revealed is not None:

        return (
            condition.fact_revealed
            in state.revealed_interests
        )

    if condition.player_intent is not None:

        return (
            state.current_player_intent
            == condition.player_intent
        )

    if condition.concessions_applied is not None:

        operator = condition.concessions_applied.get(
            "operator",
            "==",
        )

        expected = condition.concessions_applied.get(
            "value",
            0,
        )

        actual = len(
            state.applied_concessions
        )

        return compare(
            actual,
            operator,
            expected,
        )

    if condition.turn is not None:

        operator = condition.turn.get(
            "operator",
            "==",
        )

        expected = condition.turn.get(
            "value",
            0,
        )

        return compare(
            state.turn,
            operator,
            expected,
        )

    return False


def evaluate_condition_group(
    group: ConditionGroup,
    state: NegotiationState,
) -> bool:

    if group.all is not None:

        return all(
            evaluate_condition(
                condition,
                state,
            )
            for condition in group.all
        )

    if group.any is not None:

        return any(
            evaluate_condition(
                condition,
                state,
            )
            for condition in group.any
        )

    return False