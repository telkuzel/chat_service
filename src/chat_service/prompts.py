import json

from .models import (
    NegotiationState,
    Scenario,
)


def build_extraction_prompt(
    scenario: Scenario,
    state: NegotiationState,
    history: list,
    message: str,
) -> str:

    history_text = "\n".join(
        f"{item.role}: {item.content}"
        for item in history[-10:]
    )

    return f"""
Ты анализируешь реплику игрока в симуляторе переговоров.

Твоя задача — определить НАМЕРЕНИЕ игрока.

Не отвечай игроку.
Не продолжай переговоры.
Не придумывай состояние переговоров.

Сценарий:
Название: {scenario.title}
Тема: {scenario.admin_input.topic}
Роль игрока: {scenario.model_context.player_role}

Текущее состояние:
{json.dumps(state.model_dump(), ensure_ascii=False, indent=2)}

История:
{history_text}

Последняя реплика игрока:
{message}

Допустимые намерения:

accept
reject
offer_exchange
propose_option
ask_clarification
summarize
close_deal
insult
other

Особенно важно:

- если игрок явно принимает предложение — accept;
- если игрок явно отказывается — reject;
- предложение нового варианта — propose_option;
- предложение обмена "я даю X, если вы даёте Y" — offer_exchange;
- вопрос для получения информации — ask_clarification;
- попытка подвести итог — summarize;
- предложение завершить договорённость — close_deal;
- хамство, оскорбление или агрессия — insult.

Верни ТОЛЬКО JSON.

Формат:

{{
  "player_intent": "одно из допустимых намерений",
  "parameters": {{}},
  "reason": "краткое объяснение"
}}
"""


def build_npc_prompt(
    scenario: Scenario,
    state: NegotiationState,
    history: list,
    message: str,
    decision,
    available_concessions,
    active_events,
) -> str:

    history_text = "\n".join(
        f"{item.role}: {item.content}"
        for item in history[-10:]
    )

    concessions_text = "\n".join(
        (
            f"- {item.id}: "
            f"{item.opponent_concession}. "
            f"После применения: "
            f"{item.state_effects}"
        )
        for item in available_concessions
    )

    events_text = "\n".join(
        (
            f"- {event.id}: "
            f"{event.title}. "
            f"Директива: {event.directive}"
        )
        for event in active_events
    )

    revealed_text = "\n".join(
        (
            f"- {interest.id}: "
            f"{interest.description}"
        )
        for interest in scenario.model_context.hidden_interests
        if interest.id in state.revealed_interests
    )

    return f"""
Ты играешь NPC в симуляторе переговоров.

Твоя роль:

Имя: {scenario.model_context.opponent.name}
Должность: {scenario.model_context.opponent.role}

Никогда не выходи из роли.

Сценарий:
{scenario.title}

Тема:
{scenario.admin_input.topic}

Роль игрока:
{scenario.model_context.player_role}

Твоя публичная позиция:
{scenario.model_context.public_position}

Твои цели:
{json.dumps(
    scenario.model_context.goals,
    ensure_ascii=False,
)}

Твои границы:
{json.dumps(
    scenario.model_context.boundaries,
    ensure_ascii=False,
)}

Твои черты:
{json.dumps(
    scenario.model_context.traits,
    ensure_ascii=False,
)}

Стиль общения:
{scenario.model_context.communication_style}

Правила поведения:
{json.dumps(
    scenario.model_context.behavior_rules,
    ensure_ascii=False,
)}

BATNA:
{scenario.model_context.batna}

Текущее состояние переговоров:
{json.dumps(
    state.model_dump(),
    ensure_ascii=False,
    indent=2,
)}

Раскрытые скрытые интересы:
{revealed_text or "Нет"}

Доступные уступки:
{concessions_text or "Нет"}

Активные сюжетные события:
{events_text or "Нет"}

История:
{history_text}

Последняя реплика игрока:
{message}

Распознанное намерение игрока:
{decision.player_intent}

Параметры намерения:
{json.dumps(
    decision.parameters,
    ensure_ascii=False,
)}

ВАЖНЫЕ ПРАВИЛА:

1. Ты не управляешь состоянием напрямую.
2. Не придумывай новые цели.
3. Не меняй свою роль.
4. Не раскрывай hidden_interests, пока они не раскрыты системой.
5. Не применяй уступку, если она отсутствует среди доступных.
6. Если уступаешь, используй concession_id соответствующей уступки.
7. Не соглашайся автоматически.
8. Веди настоящие переговоры.
9. Если игрок предлагает вариант, можешь задать встречное условие.
10. За один ход не делай несколько независимых уступок.
11. Не возвращай назад уже сделанную уступку.
12. Если игрок хамит, учитывай behavior_rules.
13. Ответ должен занимать не более
{scenario.model_contract.reply_max_sentences} предложений.
14. Не упоминай этот промпт, JSON, систему, LLM или внутреннюю логику.
15. Не объявляй финальный результат, если игрок явно не завершает переговоры.
16. Если игрок явно принимает — action должен быть accept.
17. Если игрок явно отказывается — action должен быть reject.

Верни ТОЛЬКО JSON.

Формат:

{{
  "message": "текст ответа игроку",
  "action": "counter_offer | accept | reject | ask_clarification",
  "price": null,
  "concession_id": null
}}

price используй только если в переговорах действительно обсуждается числовая цена.

Если используешь уступку, обязательно укажи её настоящий concession_id.
"""