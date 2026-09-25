from .models import NegotiationState, Scenario


def create_initial_state(
    scenario: Scenario,
) -> NegotiationState:

    metrics = {
        name: config.start
        for name, config in scenario.state_model.metrics.items()
    }

    return NegotiationState(
        turn=0,
        turns_remaining=scenario.state_model.turns_remaining,
        metrics=metrics,
        revealed_interests=[],
        applied_concessions=[],
        triggered_plot_events=[],
        current_player_intent=None,
        current_opponent_action=None,
        outcome=None,
    )


def apply_metric_effects(
    scenario: Scenario,
    state: NegotiationState,
    effects: dict[str, int],
) -> NegotiationState:

    for metric_name, effect in effects.items():

        config = scenario.state_model.metrics.get(
            metric_name
        )

        if config is None:
            continue

        # Ограничение изменения за один ход
        effect = max(
            -config.per_turn_limit,
            min(
                config.per_turn_limit,
                effect,
            ),
        )

        current_value = state.metrics.get(
            metric_name,
            config.start,
        )

        new_value = current_value + effect

        # Ограничение диапазона
        new_value = max(
            config.min,
            min(
                config.max,
                new_value,
            ),
        )

        state.metrics[metric_name] = new_value

    return state


def advance_turn(
    state: NegotiationState,
) -> NegotiationState:

    state.turn += 1

    state.turns_remaining = max(
        0,
        state.turns_remaining - 1,
    )

    return state