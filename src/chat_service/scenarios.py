import json
from pathlib import Path

from .models import NegotiationRules, Participant, Scenario


SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


def ensure_scenarios_dir() -> None:
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)


def save_scenario(scenario: Scenario) -> None:
    ensure_scenarios_dir()
    filename = "".join(c if c.isalnum() or c in "-_" else "_" for c in scenario.name).strip("_")
    if not filename:
        filename = "scenario"
    path = SCENARIOS_DIR / f"{filename}.json"
    path.write_text(
        json.dumps(scenario.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_scenarios() -> list[Scenario]:
    ensure_scenarios_dir()
    result = []
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        try:
            result.append(Scenario.model_validate(json.loads(path.read_text(encoding="utf-8"))))
        except Exception as exc:
            print(f"[Предупреждение] Не удалось загрузить {path.name}: {exc}")
    return result


def input_optional(prompt: str) -> str:
    return input(prompt).strip()


def create_scenario_interactively() -> Scenario:
    print("\n=== Создание сценария ===")
    name = input("Название сценария: ").strip()
    description = input("Описание ситуации: ").strip()

    print("\n--- Пользователь ---")
    user = Participant(
        name=input("Имя: ").strip(),
        role=input("Роль: ").strip(),
        background=input("Опыт/контекст: ").strip(),
        goal=input("Чего хочет добиться: ").strip(),
        initial_position=input("Начальная позиция: ").strip(),
        hidden_information=input_optional("Скрытая информация (не показывается NPC): "),
    )

    print("\n--- Оппонент ---")
    opponent = Participant(
        name=input("Имя: ").strip(),
        role=input("Роль: ").strip(),
        background=input("Опыт/контекст: ").strip(),
        goal=input("Чего хочет добиться: ").strip(),
        initial_position=input("Начальная позиция: ").strip(),
        hidden_information=input_optional("Скрытая информация NPC (не показывается пользователю): "),
    )

    print("\n--- Правила (можно оставить пустыми) ---")
    rules = NegotiationRules(
        min_price=_optional_int("Минимальная цена NPC: "),
        max_price=_optional_int("Максимальная цена: "),
        min_duration_months=_optional_int("Минимальный срок, мес.: "),
        max_duration_months=_optional_int("Максимальный срок, мес.: "),
        max_concession_per_turn=_optional_int("Максимальная уступка за ход: "),
    )

    scenario = Scenario(
        name=name,
        description=description,
        user=user,
        opponent=opponent,
        rules=rules,
    )
    save_scenario(scenario)
    print(f"\nСценарий сохранён в scenarios/.")
    return scenario


def _optional_int(prompt: str) -> int | None:
    value = input(prompt).strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        print("Некорректное число — значение оставлено пустым.")
        return None
