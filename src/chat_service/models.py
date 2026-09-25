from typing import Any, Literal

from pydantic import BaseModel, Field


class AdminInput(BaseModel):
    domain: str
    topic: str
    difficulty: int
    opponent_tone: str
    opponent_position: str


class Opponent(BaseModel):
    name: str
    role: str


class HiddenInterest(BaseModel):
    id: str
    description: str
    reveal_when: str


class ModelContext(BaseModel):
    player_role: str
    opponent: Opponent
    communication_style: str
    traits: list[str]
    public_position: str
    goals: list[str]
    hidden_interests: list[HiddenInterest]
    boundaries: list[str]
    behavior_rules: list[str]
    opening_line: str
    batna: str
    known_player_facts: list[str]


class MetricConfig(BaseModel):
    min: int
    max: int
    start: int
    per_turn_limit: int


class StateModelConfig(BaseModel):
    metrics: dict[str, MetricConfig]
    turns_remaining: int
    hostility_reaction: str


class Condition(BaseModel):
    metric: str | None = None
    operator: str | None = None
    value: Any | None = None

    fact_revealed: str | None = None

    player_intent: str | None = None

    concessions_applied: dict[str, Any] | None = None

    turn: dict[str, Any] | None = None


class ConditionGroup(BaseModel):
    all: list[Condition] | None = None
    any: list[Condition] | None = None


class ConcessionWhen(BaseModel):
    all: list[Condition]


class ConcessionPath(BaseModel):
    id: str

    when: ConcessionWhen

    opponent_concession: str

    state_effects: dict[str, int] = Field(
        default_factory=dict
    )

    unlocks: str | None = None


class PlotEvent(BaseModel):
    id: str
    title: str
    directive: str

    when: ConditionGroup

    force_at_turn: int | None = None

    state_effects: dict[str, int] = Field(
        default_factory=dict
    )


class TerminationRule(BaseModel):
    outcome_id: str
    priority: int
    when: ConditionGroup


class ModelContract(BaseModel):
    language: str
    response_schema: str
    reply_max_sentences: int
    reveal_policy: str
    forbidden: list[str]


class Scenario(BaseModel):
    schema_version: str
    id: str
    title: str

    admin_input: AdminInput
    model_context: ModelContext
    state_model: StateModelConfig

    concession_paths: list[ConcessionPath] = Field(
        default_factory=list
    )

    plot_events: list[PlotEvent] = Field(
        default_factory=list
    )

    termination_rules: list[TerminationRule] = Field(
        default_factory=list
    )

    model_contract: ModelContract


class NegotiationState(BaseModel):
    turn: int = 0

    turns_remaining: int

    metrics: dict[str, int]

    revealed_interests: list[str] = Field(
        default_factory=list
    )

    applied_concessions: list[str] = Field(
        default_factory=list
    )

    triggered_plot_events: list[str] = Field(
        default_factory=list
    )

    current_player_intent: str | None = None

    current_opponent_action: str | None = None

    outcome: str | None = None


class PlayerDecision(BaseModel):
    player_intent: str

    parameters: dict[str, Any] = Field(
        default_factory=dict
    )

    reason: str = ""


class NPCResponse(BaseModel):
    message: str

    action: Literal[
        "counter_offer",
        "accept",
        "reject",
        "ask_clarification",
    ]

    price: int | float | None = None

    concession_id: str | None = None


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


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