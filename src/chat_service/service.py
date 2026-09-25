from .concessions import (
    apply_concession,
    get_available_concessions,
)
from .models import (
    ChatRequest,
    ChatResponse,
    Message,
    NPCResponse,
    PlayerDecision,
)
from .plot_events import (
    apply_plot_event,
    get_available_plot_events,
    reveal_interest,
)
from .prompts import (
    build_extraction_prompt,
    build_npc_prompt,
)
from .state import (
    advance_turn,
)
from .termination import (
    force_outcome,
)


class ChatService:

    def __init__(self, client):
        self.client = client

    def process_message(
        self,
        request: ChatRequest,
    ) -> ChatResponse:

        scenario = request.scenario
        state = request.state
        history = request.history
        message = request.message

        # -------------------------------------------------
        # 1. Если переговоры уже закончены
        # -------------------------------------------------

        if state.outcome is not None:

            return ChatResponse(
                message=Message(
                    role="assistant",
                    content=(
                        "Переговоры уже завершены."
                    ),
                ),
                state=state,
            )

        # -------------------------------------------------
        # 2. Распознаём намерение игрока
        # -------------------------------------------------

        extraction_prompt = build_extraction_prompt(
            scenario=scenario,
            state=state,
            history=history,
            message=message,
        )

        raw_decision = self.client.ask_json(
            extraction_prompt
        )

        decision = PlayerDecision.model_validate(
            raw_decision
        )

        # -------------------------------------------------
        # 3. Запоминаем намерение
        # -------------------------------------------------

        state.current_player_intent = (
            decision.player_intent
        )

        # -------------------------------------------------
        # 4. Явное принятие / отказ
        # -------------------------------------------------

        if decision.player_intent == "accept":

            state.current_opponent_action = "accept"

            state.outcome = "agreement"

            return ChatResponse(
                message=Message(
                    role="assistant",
                    content=(
                        "Договорённость принята. "
                        "Переговоры завершены."
                    ),
                ),
                state=state,
            )

        if decision.player_intent == "reject":

            state.current_opponent_action = "reject"

            state.outcome = "breakdown"

            return ChatResponse(
                message=Message(
                    role="assistant",
                    content=(
                        "Хорошо, тогда на этом "
                        "переговоры завершим."
                    ),
                ),
                state=state,
            )

        # -------------------------------------------------
        # 5. Продвигаем ход
        # -------------------------------------------------

        advance_turn(state)

        # -------------------------------------------------
        # 6. Проверяем специальные сюжетные события
        # -------------------------------------------------

        active_events = get_available_plot_events(
            scenario,
            state,
        )

        for event in active_events:

            apply_plot_event(
                scenario,
                state,
                event.id,
            )

        # -------------------------------------------------
        # 7. Определяем доступные уступки
        # -------------------------------------------------

        available_concessions = (
            get_available_concessions(
                scenario,
                state,
            )
        )

        # -------------------------------------------------
        # 8. Генерируем ответ NPC
        # -------------------------------------------------

        npc_prompt = build_npc_prompt(
            scenario=scenario,
            state=state,
            history=history,
            message=message,
            decision=decision,
            available_concessions=(
                available_concessions
            ),
            active_events=active_events,
        )

        raw_response = self.client.ask_json(
            npc_prompt
        )

        npc_response = NPCResponse.model_validate(
            raw_response
        )

        # -------------------------------------------------
        # 9. Применяем действие NPC
        # -------------------------------------------------

        state.current_opponent_action = (
            npc_response.action
        )

        if npc_response.concession_id:

            concession = apply_concession(
                scenario,
                state,
                npc_response.concession_id,
            )

            # Если LLM попытался применить
            # недоступную уступку — игнорируем её.
            if concession is None:
                npc_response.concession_id = None

        # -------------------------------------------------
        # 10. Обрабатываем insult
        # -------------------------------------------------

        if decision.player_intent == "insult":

            # Пока применяем penalty к trust.
            # hostility_reaction из сценария
            # определяет, что это вообще допустимо.

            if (
                scenario.state_model
                .hostility_reaction
                == "penalty"
            ):
                current_trust = state.metrics.get(
                    "trust"
                )

                if current_trust is not None:
                    state.metrics["trust"] = max(
                        0,
                        current_trust - 10,
                    )

        # -------------------------------------------------
        # 11. Проверяем скрытые интересы
        # -------------------------------------------------

        self._process_interest_reveals(
            scenario,
            state,
            decision,
        )

        # -------------------------------------------------
        # 12. Проверяем завершение
        # -------------------------------------------------

        self._check_default_termination(
            scenario,
            state,
        )

        # -------------------------------------------------
        # 13. Возвращаем результат
        # -------------------------------------------------

        return ChatResponse(
            message=Message(
                role="assistant",
                content=npc_response.message,
            ),
            state=state,
        )

    @staticmethod
    def _process_interest_reveals(
        scenario,
        state,
        decision,
    ):

        """
        reveal_when в текущем JSON является
        естественно-языковым описанием.

        Поэтому здесь используем безопасные
        эвристики по намерению игрока.

        В дальнейшем это можно вынести
        в отдельную систему правил.
        """

        if (
            "interest_1"
            not in state.revealed_interests
            and decision.player_intent
            == "ask_clarification"
        ):
            reveal_interest(
                state,
                "interest_1",
            )

        if (
            "interest_2"
            not in state.revealed_interests
            and decision.player_intent
            == "summarize"
        ):
            reveal_interest(
                state,
                "interest_2",
            )

    @staticmethod
    def _check_default_termination(
        scenario,
        state,
    ):

        if state.outcome is not None:
            return

        # Критические состояния
        trust = state.metrics.get(
            "trust"
        )

        tension = state.metrics.get(
            "tension"
        )

        if trust is not None and trust <= 10:
            force_outcome(
                state,
                "breakdown",
            )
            return

        if tension is not None and tension >= 90:
            force_outcome(
                state,
                "breakdown",
            )
            return

        # Истёк лимит ходов
        if state.turns_remaining <= 0:
            force_outcome(
                state,
                "timeout",
            )