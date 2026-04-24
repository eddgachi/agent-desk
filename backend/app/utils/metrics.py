from prometheus_client import Counter, Gauge, Histogram

# ── Simulation Metrics ───────────────────────────────────
SIM_TICKS_TOTAL = Counter(
    "sim_ticks_total",
    "Total number of simulation ticks processed",
    ["sim_id"]
)

SIM_AGENTS_ACTIVE = Gauge(
    "sim_agents_active",
    "Number of active agents in the simulation",
    ["sim_id"]
)

SIM_TASKS_COMPLETED_TOTAL = Counter(
    "sim_tasks_completed_total",
    "Total number of tasks completed",
    ["sim_id"]
)

# ── LLM Metrics ──────────────────────────────────────────
LLM_CALLS_TOTAL = Counter(
    "llm_calls_total",
    "Total number of LLM calls made",
    ["sim_id", "agent_id", "call_type"]
)

LLM_LATENCY_SECONDS = Histogram(
    "llm_latency_seconds",
    "Time taken for LLM calls",
    ["sim_id", "call_type"]
)

LLM_COST_ESTIMATE = Counter(
    "llm_cost_estimate",
    "Estimated cost of LLM calls (based on tokens)",
    ["sim_id"]
)

LLM_DECISIONS_VALID = Counter(
    "llm_decisions_valid_total",
    "Total number of valid vs invalid LLM decisions",
    ["sim_id", "is_valid"]
)

# ── Agent Metrics ─────────────────────────────────────────
AGENT_ENERGY_LEVEL = Gauge(
    "agent_energy_level",
    "Current energy level of an agent",
    ["sim_id", "agent_id"]
)

AGENT_FOCUS_LEVEL = Gauge(
    "agent_focus_level",
    "Current focus level of an agent",
    ["sim_id", "agent_id"]
)
