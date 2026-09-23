from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Action(str, Enum):
    COUNTER_OFFER = "counter_offer"
    ACCEPT = "accept"
    REJECT = "reject"
    ASK_CLARIFICATION = "ask_clarification"


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class NegotiationStyle(BaseModel):
    flexibility: Literal["low", "medium", "high"] = "medium"

    concession_size: int | None = None

    requires_justification: bool = False

    can_offer_alternatives: bool = True

    alternative_offers: list[str] = Field(default_factory=list)

    description: str = ""


class Participant(BaseModel):
    name: str
    role: str
    background: str
    goal: str
    initial_position: str

    # Информация, которую нельзя раскрывать пользователю
    hidden_information: dict[str, str | int | float | bool] = Field(
        default_factory=dict
    )

    opening_message: str = ""

    negotiation_style: NegotiationStyle = Field(
        default_factory=NegotiationStyle
    )


class NegotiationRules(BaseModel):
    max_opponent_salary: int | None = None
    max_concession_per_turn: int | None = None


class Scenario(BaseModel):
    name: str
    description: str

    player: Participant
    opponent: Participant

    rules: NegotiationRules = Field(
        default_factory=NegotiationRules
    )


class NegotiationState(BaseModel):
    status: Literal[
        "in_progress",
        "accepted",
        "rejected"
    ] = "in_progress"

    current_price: int | None = None

    last_user_price: int | None = None

    last_opponent_price: int | None = None


class Decision(BaseModel):
    action: Action

    price: int | None = None

    reason: str = ""

class NPCResponse(BaseModel):
    message: str

    action: Action

    price: int | None = None

class ChatRequest(BaseModel):
    scenario: Scenario

    state: NegotiationState

    history: list[Message] = Field(
        default_factory=list
    )

    message: str


class ChatResponse(BaseModel):
    message: Message

    state: NegotiationState

    decision: Decision