from .gigachat_client import GigaChatClient
from .models import (
    ChatRequest,
    ChatResponse,
    Decision,
    Message,
    Action,
    NPCResponse,
)
from .prompts import (
    build_extraction_prompt,
    build_response_prompt,
)
from .validator import (
    validate_decision,
)


class ChatService:

    def __init__(self, llm: GigaChatClient):
        self.llm = llm

    def process_message(
        self,
        request: ChatRequest,
    ) -> ChatResponse:

        # ----------------------------------------------
        # 1. Анализируем сообщение пользователя
        # ----------------------------------------------

        extraction_prompt = build_extraction_prompt(
            scenario=request.scenario,
            state=request.state,
            message=request.message,
        )

        raw_decision = self.llm.ask_json(
            extraction_prompt
        )

        decision = Decision.model_validate(
            raw_decision
        )

        # ----------------------------------------------
        # 2. Проверяем решение
        # ----------------------------------------------

        valid, validation_message = validate_decision(
            scenario=request.scenario,
            state=request.state,
            decision=decision,
        )

        # ----------------------------------------------
        # 3. ACCEPT
        # ----------------------------------------------

        if (
            valid
            and decision.action == Action.ACCEPT
        ):

            new_state = request.state.model_copy(
                deep=True
            )

            new_state.status = "accepted"

            response_text = (
                "Хорошо, договорились. "
                "Я принимаю ваши условия."
            )

            return ChatResponse(
                message=Message(
                    role="assistant",
                    content=response_text,
                ),
                state=new_state,
                decision=decision,
            )

        # ----------------------------------------------
        # 4. REJECT
        # ----------------------------------------------

        if (
            valid
            and decision.action == Action.REJECT
        ):

            new_state = request.state.model_copy(
                deep=True
            )

            new_state.status = "rejected"

            response_text = (
                "Понимаю. В таком случае "
                "мы не сможем договориться."
            )

            return ChatResponse(
                message=Message(
                    role="assistant",
                    content=response_text,
                ),
                state=new_state,
                decision=decision,
            )

        # ----------------------------------------------
        # 5. Если решение невалидно
        # ----------------------------------------------

        if not valid:

            decision_for_llm = {
                "action": decision.action.value,
                "price": decision.price,
                "reason": decision.reason,
                "validation": {
                    "valid": False,
                    "message": validation_message,
                },
            }

        else:

            decision_for_llm = {
                "action": decision.action.value,
                "price": decision.price,
                "reason": decision.reason,
                "validation": {
                    "valid": True,
                    "message": validation_message,
                },
            }

        # ----------------------------------------------
        # 6. Генерируем ответ NPC
        # ----------------------------------------------

        response_prompt = build_response_prompt(
            scenario=request.scenario,
            state=request.state,
            history=request.history,
            message=request.message,
            decision=decision_for_llm,
        )

        raw_response = self.llm.ask_json(
            response_prompt
        )

        npc_response = NPCResponse.model_validate(
            raw_response
        )

        # ----------------------------------------------
        # 7. Обновляем state
        # ----------------------------------------------

        new_state = request.state.model_copy(
            deep=True
        )

        if npc_response.action == Action.COUNTER_OFFER:

            if npc_response.price is not None:

                new_state.current_price = npc_response.price

                new_state.last_opponent_price = (
                    npc_response.price
                )

        # Если NPC ответил встречным предложением,
        # пока здесь оставляем текущую цену.
        #
        # Позже можно добавить отдельный extraction
        # ответа NPC или structured response.

        return ChatResponse(
            message=Message(
                role="assistant",
                content=npc_response.message,
            ),
            state=new_state,
            decision=decision,
        )