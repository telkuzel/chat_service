from .conditions import evaluate_condition_group
from .models import (
    ConcessionPath,
    NegotiationState,
    Scenario,
)
from .state import apply_metric_effects


def get_available_concessions(
    scenario: Scenario,
    state: NegotiationState,
) -> list[ConcessionPath]:

    result = []

    for concession in scenario.concession_paths:

        if concession.id in state.applied_concessions:
            continue

        if evaluate_condition_group(
            concession.when,
            state,
        ):
            result.append(concession)

    return result


def apply_concession(
    scenario: Scenario,
    state: NegotiationState,
    concession_id: str,
) -> ConcessionPath | None:

    concession = next(
        (
            item
            for item in scenario.concession_paths
            if item.id == concession_id
        ),
        None,
    )

    if concession is None:
        return None

    if concession.id in state.applied_concessions:
        return None

    if not evaluate_condition_group(
        concession.when,
        state,
    ):
        return None

    apply_metric_effects(
        scenario,
        state,
        concession.state_effects,
    )

    state.applied_concessions.append(
        concession.id
    )

    return concession