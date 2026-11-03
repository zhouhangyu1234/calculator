/* Lab 7 frontend logic.
 *
 * Every request uses a RELATIVE url ("/api/calc", "/health") on purpose:
 * inside Docker, "localhost" would be the nginx container itself, and the
 * browser cannot resolve the Compose service name "backend" at all.
 * The nginx config in this container proxies /api/ to http://backend:8000,
 * so the service name is resolved inside the Docker network.
 */
const API = "/api/calc";
const HEALTH = "/health";
const MAX_HISTORY = 6;

const state = {
    left: null,        // first operand, kept as a string
    op: null,          // pending operator ("+" "-" "*" "/")
    current: "0",      // what the display shows
    typing: false,     // true once the user started typing an operand
    busy: false
};

const displayEl = document.getElementById("display");
const expressionEl = document.getElementById("expression");
const historyEl = document.getElementById("history");
const statusEl = document.getElementById("status");
const statusTextEl = document.getElementById("status-text");

const SYMBOL = { "+": "+", "-": "−", "*": "×", "/": "÷" };

/* ------------------------------------------------------------------ render */

function render() {
    displayEl.textContent = state.current;
    displayEl.classList.toggle("screen__value--error", state.error === true);
    expressionEl.textContent = state.left !== null && state.op
        ? `${state.left} ${SYMBOL[state.op]}${state.typing ? " " + state.current : ""}`
        : "\u00a0";
}

function showError(message) {
    state.current = message;
    state.error = true;
    state.typing = false;
    render();
}

/* ------------------------------------------------------------------ input */

function inputDigit(digit) {
    if (state.error) {
        reset();
    }
    if (!state.typing) {
        state.current = digit === "." ? "0." : digit;
        state.typing = true;
    } else if (digit === ".") {
        if (!state.current.includes(".")) {
            state.current += ".";
        }
    } else if (state.current === "0") {
        state.current = digit;
    } else {
        state.current += digit;
    }
    render();
}

function chooseOperator(op) {
    if (state.error) {
        reset();
    }
    // Chained input: 2 + 3 + ... evaluates the pending operation first.
    if (state.left !== null && state.op && state.typing) {
        equals();
    }
    state.left = state.current;
    state.op = op;
    state.typing = false;
    render();
}

function backspace() {
    if (state.error || !state.typing) {
        state.current = "0";
        state.typing = false;
        render();
        return;
    }
    state.current = state.current.length > 1 ? state.current.slice(0, -1) : "0";
    if (state.current === "-") {
        state.current = "0";
    }
    render();
}

function negate() {
    if (state.current === "0") {
        return;
    }
    state.current = state.current.startsWith("-")
        ? state.current.slice(1)
        : "-" + state.current;
    render();
}

function reset() {
    state.left = null;
    state.op = null;
    state.current = "0";
    state.typing = false;
    state.error = false;
    render();
}

/* --------------------------------------------------------------- network */

async function equals() {
    if (state.left === null || !state.op) {
        return;
    }
    const left = state.left;
    const right = state.current;
    const op = state.op;

    state.busy = true;
    try {
        const url = `${API}?a=${encodeURIComponent(left)}&op=${encodeURIComponent(op)}&b=${encodeURIComponent(right)}`;
        const response = await fetch(url, { headers: { Accept: "application/json" } });
        const data = await response.json();

        if (!response.ok || !data.ok) {
            showError(data.error || `HTTP ${response.status}`);
            addHistory(`${left} ${SYMBOL[op]} ${right}`, data.error || "error", true);
            return;
        }

        const result = String(data.result);
        addHistory(`${left} ${SYMBOL[op]} ${right}`, result, false);
        state.left = null;
        state.op = null;
        state.current = result;
        state.typing = false;
        state.error = false;
        render();
    } catch (e) {
        showError("Cannot reach the backend service");
    } finally {
        state.busy = false;
    }
}

async function checkHealth() {
    try {
        const response = await fetch(HEALTH, { headers: { Accept: "application/json" } });
        const data = await response.json();
        statusEl.classList.remove("status--pending", "status--down");
        statusEl.classList.add("status--ok");
        statusTextEl.textContent = `${data.service} ok · LOG_LEVEL=${data.logLevel}`;
    } catch (e) {
        statusEl.classList.remove("status--pending", "status--ok");
        statusEl.classList.add("status--down");
        statusTextEl.textContent = "backend unreachable";
    }
}

function addHistory(expression, result, isError) {
    const empty = historyEl.querySelector(".history__empty");
    if (empty) {
        empty.remove();
    }
    const li = document.createElement("li");
    li.innerHTML = `<span>${expression}</span><b>${result}</b>`;
    if (isError) {
        li.querySelector("b").style.color = "var(--err)";
    }
    historyEl.prepend(li);
    while (historyEl.children.length > MAX_HISTORY) {
        historyEl.lastElementChild.remove();
    }
}

/* ------------------------------------------------------------------ events */

document.querySelector(".keypad").addEventListener("click", (event) => {
    const key = event.target.closest(".key");
    if (!key) {
        return;
    }
    const value = key.dataset.key;
    if (value === "clear") {
        reset();
    } else if (value === "back") {
        backspace();
    } else if (value === "neg") {
        negate();
    } else if (value === "equals") {
        equals();
    } else if (value.startsWith("op:")) {
        chooseOperator(value.slice(3));
    } else {
        inputDigit(value);
    }
});

document.addEventListener("keydown", (event) => {
    const map = { "*": "op:*", "/": "op:/", "-": "op:-", "+": "op:+" };
    if (/^[0-9.]$/.test(event.key)) {
        inputDigit(event.key);
    } else if (map[event.key]) {
        chooseOperator(map[event.key].slice(3));
    } else if (event.key === "Enter" || event.key === "=") {
        equals();
    } else if (event.key === "Backspace") {
        backspace();
    } else if (event.key === "Escape") {
        reset();
    }
});

render();
checkHealth();
