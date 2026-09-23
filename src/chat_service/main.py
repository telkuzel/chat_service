from .gigachat_client import GigaChatClient
from .models import Action, Decision, NegotiationState, OpponentResponse, Scenario
from .prompts import extraction_prompt, response_prompt
from .scenarios import create_scenario_interactively, load_scenarios
from .validator import apply_valid_decision, validate_decision


def print_scenario(scenario: Scenario) -> None:
    print("\n=== Сценарий ===")
    print(f"{scenario.name}: {scenario.description}")

    print(f"\nВы: {scenario.user.name}, {scenario.user.role}")
    print(f"Контекст: {scenario.user.background}")
    print(f"Цель: {scenario.user.goal}")
    print(f"Позиция: {scenario.user.initial_position}")
    if scenario.user.hidden_information:
        print(f"Ваша личная информация: {scenario.user.hidden_information}")

    print(f"\nОппонент: {scenario.opponent.name}, {scenario.opponent.role}")
    print(f"Цель оппонента: {scenario.opponent.goal}")
    print(f"Позиция оппонента: {scenario.opponent.initial_position}")
    print("Скрытая информация оппонента вам не показывается.")

    if scenario.rules.min_price is not None:
        print(f"\nВаш минимально приемлемый уровень цены: {scenario.rules.min_price}")
    if scenario.rules.min_duration_months is not None:
        print(f"Ваш минимально приемлемый срок: {scenario.rules.min_duration_months} мес.")


def choose_scenario() -> Scenario:
    scenarios = load_scenarios()

    print("=== Negotiation Simulator ===")
    print("1. Создать новый сценарий")
    if scenarios:
        print("2. Выбрать существующий сценарий")
    else:
        print("Сохранённых сценариев пока нет.")

    choice = input("\nВыбор: ").strip()

    if choice == "1":
        return create_scenario_interactively()

    if choice == "2" and scenarios:
        print("\nСценарии:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. {scenario.name} — {scenario.description}")
        index = int(input("Номер сценария: ")) - 1
        return scenarios[index]

    print("Некорректный выбор.")
    return choose_scenario()


def main() -> None:
    scenario = choose_scenario()
    print_scenario(scenario)

    client = GigaChatClient()
    state = NegotiationState(
        current_price=scenario.rules.initial_opponent_price,
        current_duration_months=scenario.rules.initial_opponent_duration_months,
    )

    print("\n=== Переговоры ===")
    print("Введите /quit для выхода.")
    print("Минимальные условия — это ваши ориентиры, а не автоматическое решение.")
    print("Только ваше явное согласие завершает переговоры успешно.\n")

    if state.current_price is not None or state.current_duration_months is not None:
        parts = []
        if state.current_price is not None:
            parts.append(f"зарплата {state.current_price} ₽")
        if state.current_duration_months is not None:
            parts.append(f"срок {state.current_duration_months} мес.")
        print(f"{scenario.opponent.name}: Задравствуйте, спасибо что пришли на собеседование мы предлагаем: {', '.join(parts)}.")
    else:
        print(f"{scenario.opponent.name}: Давайте обсудим условия.")

    while not state.finished:
        user_message = input("\nВы: ").strip()
        if not user_message:
            continue
        if user_message.lower() in {"/quit", "/exit"}:
            break

        try:
            raw = client.extract_json(extraction_prompt(user_message, scenario, state))
            decision = Decision.model_validate(raw)
            errors = validate_decision(decision, state, scenario.rules)

            if errors:
                validation_result = "РЕШЕНИЕ НЕДОПУСТИМО:\n- " + "\n- ".join(errors)
            else:
                validation_result = "РЕШЕНИЕ ДОПУСТИМО."

            # Player acceptance/rejection is applied before the NPC response so
            # the NPC knows that it must not continue the negotiation after ACCEPT.
            if not errors and decision.action in {Action.ACCEPT, Action.REJECT}:
                apply_valid_decision(decision, state)

            response_raw = client.extract_json(
                response_prompt(
                    user_message,
                    decision.model_dump_json(),
                    scenario,
                    state,
                    validation_result,
                )
            )
            opponent_response = OpponentResponse.model_validate(response_raw)

            # If the player accepted, do not allow the LLM to invent a new offer.
            if decision.action == Action.ACCEPT and not errors:
                print(f"\n{scenario.opponent.name}: {opponent_response.message}")
                print(f"\nПереговоры завершены: вы приняли условия.")
                break

            if decision.action == Action.REJECT and not errors:
                print(f"\n{scenario.opponent.name}: {opponent_response.message}")
                print("\nПереговоры завершены: вы отказались от сделки.")
                break

            # For normal negotiation turns, update the CURRENT OPPONENT OFFER
            # from structured LLM output. This fixes the old bug where the state
            # remained at the initial 160000 even after Anna offered 165000.
            if opponent_response.offer_price is not None:
                state.current_price = opponent_response.offer_price
            if opponent_response.offer_duration_months is not None:
                state.current_duration_months = opponent_response.offer_duration_months

            print(f"\n{scenario.opponent.name}: {opponent_response.message}")

        except (ValueError, IndexError) as exc:
            print(f"\n[Ошибка] {exc}")
        except Exception as exc:
            print(f"\n[Ошибка GigaChat/API] {exc}")

    if not state.finished:
        print("\nПереговоры прерваны.")


if __name__ == "__main__":
    main()
