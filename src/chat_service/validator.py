from .models import (
    Action,
    Decision,
    NegotiationState,
    Scenario,
)


def validate_decision(
    scenario: Scenario,
    state: NegotiationState,
    decision: Decision,
) -> tuple[bool, str]:

    # Переговоры уже закончены
    if state.status != "in_progress":
        return False, "Переговоры уже завершены."

    # --------------------------------------------------
    # ACCEPT
    # --------------------------------------------------

    if decision.action == Action.ACCEPT:

        if state.current_price is None:
            return False, "Нельзя принять условия без текущего предложения."

        return True, "Условия приняты."

    # --------------------------------------------------
    # REJECT
    # --------------------------------------------------

    if decision.action == Action.REJECT:

        return True, "Предложение отклонено."

    # --------------------------------------------------
    # ASK CLARIFICATION
    # --------------------------------------------------

    if decision.action == Action.ASK_CLARIFICATION:

        return True, "Уточняющий вопрос допустим."

    # --------------------------------------------------
    # COUNTER OFFER
    # --------------------------------------------------

    if decision.action == Action.COUNTER_OFFER:

        if decision.price is None:
            return False, "Встречное предложение должно содержать цену."

        price = decision.price

        max_price = scenario.rules.max_opponent_salary

        if max_price is not None and price > max_price:
            return (
                False,
                f"Цена {price} превышает максимальную допустимую "
                f"цену {max_price}."
            )

        # Проверяем максимальный размер уступки
        if (
            state.current_price is not None
            and scenario.rules.max_concession_per_turn is not None
        ):

            concession = price - state.current_price

            if concession > scenario.rules.max_concession_per_turn:

                return (
                    False,
                    "Размер уступки за один ход превышает допустимый."
                )

        return True, "Предложение допустимо."

    return False, "Неизвестное действие."


def apply_decision(
    state: NegotiationState,
    decision: Decision,
) -> NegotiationState:

    new_state = state.model_copy(deep=True)

    if decision.action == Action.ACCEPT:

        new_state.status = "accepted"

        return new_state

    if decision.action == Action.REJECT:

        new_state.status = "rejected"

        return new_state

    if decision.action == Action.COUNTER_OFFER:

        new_state.last_user_price = decision.price

    return new_state