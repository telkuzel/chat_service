from .conditions import evaluate_condition_group
from .models import (
    NegotiationState,
    PlotEvent,
    Scenario,
)
from .state import apply_metric_effects


def reveal_interest(
    state: NegotiationState,
    interest_id: str,
) -> bool:

    if interest_id in state.revealed_interests:
        return False

    state.revealed_interests.append(
        interest_id
    )

    return True


def get_available_plot_events(
    scenario: Scenario,
    state: NegotiationState,
) -> list[PlotEvent]:

    result = []

    for event in scenario.plot_events:

        if event.id in state.triggered_plot_events:
            continue

        conditions_met = evaluate_condition_group(
            event.when,
            state,
        )

        forced = (
            event.force_at_turn is not None
            and state.turn >= event.force_at_turn
        )

        if conditions_met or forced:
            result.append(event)

    return result


def apply_plot_event(
    scenario: Scenario,
    state: NegotiationState,
    event_id: str,
) -> PlotEvent | None:

    event = next(
        (
            item
            for item in scenario.plot_events
            if item.id == event_id
        ),
        None,
    )

    if event is None:
        return None

    if event.id in state.triggered_plot_events:
        return None

    conditions_met = evaluate_condition_group(
        event.when,
        state,
    )

    forced = (
        event.force_at_turn is not None
        and state.turn >= event.force_at_turn
    )

    if not conditions_met and not forced:
        return None

    apply_metric_effects(
        scenario,
        state,
        event.state_effects,
    )

    state.triggered_plot_events.append(
        event.id
    )

    return event