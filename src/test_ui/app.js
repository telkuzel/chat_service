const API_URL = "http://127.0.0.1:8000";

let scenario = null;
let state = null;
let history = [];

const chat = document.getElementById("chat");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const newDialogButton = document.getElementById("newDialogButton");

async function loadScenario() {
    try {
        const response = await fetch("./scenario.json");

        if (!response.ok) {
            throw new Error(
                `Не удалось загрузить scenario.json: ${response.status}`
            );
        }

        scenario = await response.json();

        initializeDialog();
        updateScenarioInfo();
        await checkHealth();

    } catch (error) {
        chat.innerHTML = `
            <div class="error">
                <strong>Ошибка загрузки сценария</strong>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;
    }
}

function initializeDialog() {
    state = createInitialState();
    history = [];

    chat.innerHTML = "";

    const openingLine = scenario.model_context.opening_line;

    addMessage("assistant", openingLine);

    history.push({
        role: "assistant",
        content: openingLine
    });

    updateState();

    messageInput.disabled = false;
    sendButton.disabled = false;

    messageInput.focus();
}

function createInitialState() {
    const metrics = {};

    for (const [name, config] of Object.entries(
        scenario.state_model.metrics
    )) {
        metrics[name] = config.start;
    }

    return {
        turn: 0,
        turns_remaining: scenario.state_model.turns_remaining,
        metrics: metrics,
        revealed_interests: [],
        applied_concessions: [],
        triggered_plot_events: [],
        current_player_intent: null,
        current_opponent_action: null,
        outcome: null
    };
}

function updateScenarioInfo() {
    document.getElementById("scenarioTitle").textContent =
        scenario.title;

    document.getElementById("domain").textContent =
        scenario.admin_input.domain;

    document.getElementById("topic").textContent =
        scenario.admin_input.topic;

    document.getElementById("difficulty").textContent =
        scenario.admin_input.difficulty;

    document.getElementById("playerRole").textContent =
        scenario.model_context.player_role;

    document.getElementById("opponent").textContent =
        `${scenario.model_context.opponent.name} — ${scenario.model_context.opponent.role}`;
}

function addMessage(role, content) {
    const message = document.createElement("div");
    message.className = `message ${role}`;

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";

    const roleElement = document.createElement("div");
    roleElement.className = "message-role";

    const roleName =
        role === "user"
            ? "Вы"
            : scenario?.model_context?.opponent?.name || "Оппонент";

    roleElement.textContent = roleName;

    const textElement = document.createElement("div");

    // Убираем лишние пробелы и пустые строки
    textElement.textContent = String(content)
        .replace(/\r\n/g, "\n")
        .trim();

    messageContent.appendChild(roleElement);
    messageContent.appendChild(textElement);

    message.appendChild(messageContent);
    chat.appendChild(message);

    chat.scrollTop = chat.scrollHeight;
}

async function sendMessage() {
    const text = messageInput.value.trim();

    if (!text || !scenario || !state) {
        return;
    }

    if (state.outcome) {
        return;
    }

    messageInput.value = "";

    addMessage("user", text);

    history.push({
        role: "user",
        content: text
    });

    setLoading(true);

    try {
        const response = await fetch(
            `${API_URL}/chat/message`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    scenario: scenario,
                    state: state,
                    history: history,
                    message: text
                })
            }
        );

        if (!response.ok) {
            const errorText = await response.text();

            throw new Error(
                `HTTP ${response.status}: ${errorText}`
            );
        }

        const data = await response.json();

        state = data.state;

        const assistantMessage = data.message.content;

        addMessage(
            "assistant",
            assistantMessage
        );

        history.push({
            role: "assistant",
            content: assistantMessage
        });

        updateState();

        if (state.outcome) {
            messageInput.disabled = true;
            sendButton.disabled = true;
        }

    } catch (error) {
        addMessage(
            "assistant",
            `Ошибка API: ${error.message}`
        );

        history.pop();
    } finally {
        setLoading(false);
    }
}

function setLoading(loading) {
    sendButton.disabled =
        loading || Boolean(state?.outcome);

    messageInput.disabled =
        loading || Boolean(state?.outcome);

    sendButton.textContent =
        loading ? "Ожидание..." : "Отправить";
}

async function checkHealth() {
    const status = document.getElementById("healthStatus");

    try {
        const response = await fetch(
            `${API_URL}/health`
        );

        if (!response.ok) {
            throw new Error();
        }

        status.textContent = "API: online";
        status.className = "status online";

    } catch {
        status.textContent = "API: offline";
        status.className = "status offline";
    }
}

function updateState() {
    if (!state) {
        return;
    }

    const metrics = state.metrics || {};

    updateMetric(
        "trust",
        metrics.trust
    );

    updateMetric(
        "tension",
        metrics.tension
    );

    updateMetric(
        "progress",
        metrics.progress
    );

    updateMetric(
        "readiness",
        metrics.concession_readiness
    );

    document.getElementById("turnValue").textContent =
        state.turn ?? "-";

    document.getElementById("turnsRemainingValue").textContent =
        state.turns_remaining ?? "-";

    document.getElementById("intentValue").textContent =
        state.current_player_intent || "-";

    document.getElementById("actionValue").textContent =
        state.current_opponent_action || "-";

    updateList(
        "revealedInterests",
        state.revealed_interests
    );

    updateList(
        "appliedConcessions",
        state.applied_concessions
    );

    updateList(
        "plotEvents",
        state.triggered_plot_events
    );

    const outcomeContainer =
        document.getElementById("outcomeContainer");

    const outcomeValue =
        document.getElementById("outcomeValue");

    if (state.outcome) {
        outcomeContainer.classList.remove("hidden");
        outcomeValue.textContent = state.outcome;
    } else {
        outcomeContainer.classList.add("hidden");
        outcomeValue.textContent = "-";
    }

    document.getElementById("rawState").textContent =
        JSON.stringify(state, null, 2);
}

function updateMetric(name, value) {
    const valueElement =
        document.getElementById(`${name}Value`);

    const barElement =
        document.getElementById(`${name}Bar`);

    if (value === undefined || value === null) {
        valueElement.textContent = "-";
        barElement.style.width = "0%";
        return;
    }

    valueElement.textContent = value;
    barElement.style.width = `${Math.max(0, Math.min(100, value))}%`;
}

function updateList(elementId, items) {
    const element =
        document.getElementById(elementId);

    if (!items || items.length === 0) {
        element.textContent = "Нет";
        return;
    }

    element.innerHTML = items
        .map(
            item => `
                <div class="debug-item">
                    ${escapeHtml(String(item))}
                </div>
            `
        )
        .join("");
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

sendButton.addEventListener(
    "click",
    sendMessage
);

messageInput.addEventListener(
    "keydown",
    event => {
        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {
            event.preventDefault();
            sendMessage();
        }
    }
);

newDialogButton.addEventListener(
    "click",
    () => {
        if (!scenario) {
            return;
        }

        initializeDialog();
    }
);

loadScenario();