"""Observability: structured logging and Prometheus metrics.

All logs carry ``company_id``, ``agent_id``, ``task_id``, ``trace_id``. Secrets
are never logged. Metrics are exposed at ``/metrics``.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest

EVENTS_PUBLISHED = Counter(
    "polyfloor_events_published_total", "Events published", ["company_id", "event_type"]
)
TASKS_BY_STATUS = Gauge(
    "polyfloor_tasks_by_status", "Tasks by status", ["company_id", "status"]
)
AGENTS_BY_STATE = Gauge(
    "polyfloor_agents_by_state", "Agents by state", ["company_id", "state"]
)
APPROVALS_PENDING = Gauge(
    "polyfloor_approvals_pending", "Pending approvals", ["company_id"]
)
SSE_CLIENTS = Gauge("polyfloor_sse_clients", "Active SSE clients", ["company_id"])
ROUTER_ERRORS = Counter("polyfloor_router_errors_total", "Model router errors")
TASK_LATENCY = Histogram(
    "polyfloor_task_latency_seconds", "Task stage latency", ["company_id"]
)


def metrics_text() -> str:
    return generate_latest().decode("utf-8")


def update_company_metrics(company_id: str, snapshot: dict) -> None:
    """Refresh gauges from a company state snapshot."""
    by_status: dict = snapshot.get("metrics", {}).get("tasks_by_status", {})
    for status, count in by_status.items():
        TASKS_BY_STATUS.labels(company_id=company_id, status=status).set(count)
    agents: list = snapshot.get("agents", [])
    by_state: dict[str, float] = {}
    for a in agents:
        by_state[a.get("state", "idle")] = by_state.get(a.get("state", "idle"), 0) + 1
    for state, count in by_state.items():
        AGENTS_BY_STATE.labels(company_id=company_id, state=state).set(count)
    pending = snapshot.get("metrics", {}).get("pending_approvals", 0)
    APPROVALS_PENDING.labels(company_id=company_id).set(pending)
