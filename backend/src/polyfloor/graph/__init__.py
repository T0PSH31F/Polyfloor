"""Graph state — pure-ish state transition component for task workflows.

Implements the task lifecycle as a state machine with approval pause/resume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    STAGING = "staging"
    DONE = "done"
    REJECTED = "rejected"


# Valid transitions
TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.BACKLOG: {TaskStatus.QUEUED},
    TaskStatus.QUEUED: {TaskStatus.IN_PROGRESS, TaskStatus.BACKLOG},
    TaskStatus.IN_PROGRESS: {TaskStatus.STAGING, TaskStatus.REJECTED, TaskStatus.QUEUED},
    TaskStatus.STAGING: {TaskStatus.DONE, TaskStatus.REJECTED, TaskStatus.IN_PROGRESS},
    TaskStatus.REJECTED: {TaskStatus.BACKLOG, TaskStatus.QUEUED},
    TaskStatus.DONE: {TaskStatus.BACKLOG},
}


@dataclass
class TaskState:
    """Immutable task state snapshot."""

    task_id: int
    floor_id: str
    status: TaskStatus
    assigned_role: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def can_transition_to(self, target: TaskStatus) -> bool:
        """Check if a transition to the target status is valid."""
        return target in TRANSITIONS.get(self.status, set())

    def transition_to(self, target: TaskStatus) -> "TaskState":
        """Return a new TaskState with the transitioned status.

        Raises ValueError if the transition is invalid.
        """
        if not self.can_transition_to(target):
            raise ValueError(
                f"Invalid transition: {self.status.value} -> {target.value}. "
                f"Allowed: {[s.value for s in TRANSITIONS.get(self.status, set())]}"
            )
        return TaskState(
            task_id=self.task_id,
            floor_id=self.floor_id,
            status=target,
            assigned_role=self.assigned_role,
            metadata=self.metadata,
        )


@dataclass
class ApprovalGate:
    """Represents a pending approval that blocks task progression."""

    approval_id: int
    task_id: int
    approval_type: str
    description: str
    status: str = "pending"  # pending, approved, rejected

    @property
    def is_resolved(self) -> bool:
        return self.status in ("approved", "rejected")

    @property
    def is_approved(self) -> bool:
        return self.status == "approved"


class WorkflowGraph:
    """State machine for task workflows with approval gates.

    This is a pure-ish component — it does not touch the database directly.
    Callers are responsible for persisting state changes.
    """

    def __init__(self):
        self._approval_gates: dict[int, list[ApprovalGate]] = {}  # task_id -> gates

    def add_approval_gate(self, task_id: int, gate: ApprovalGate):
        """Add an approval gate that blocks task progression."""
        self._approval_gates.setdefault(task_id, []).append(gate)

    def get_pending_gates(self, task_id: int) -> list[ApprovalGate]:
        """Get unresolved approval gates for a task."""
        return [g for g in self._approval_gates.get(task_id, []) if not g.is_resolved]

    def can_proceed(self, task_id: int) -> bool:
        """Check if a task can proceed (no pending approval gates)."""
        return len(self.get_pending_gates(task_id)) == 0

    def resolve_gate(self, task_id: int, approval_id: int, approved: bool, resolved_by: str) -> bool:
        """Resolve an approval gate. Returns True if found and resolved."""
        for gate in self._approval_gates.get(task_id, []):
            if gate.approval_id == approval_id and not gate.is_resolved:
                gate.status = "approved" if approved else "rejected"
                return True
        return False

    def try_transition(
        self,
        state: TaskState,
        target: TaskStatus,
        require_approval: bool = False,
    ) -> tuple[TaskState, Optional[str]]:
        """Attempt a state transition.

        Returns:
            (new_state, None) on success
            (original_state, error_message) on failure
        """
        if not state.can_transition_to(target):
            return state, f"Invalid transition: {state.status.value} -> {target.value}"

        if require_approval and not self.can_proceed(state.task_id):
            pending = self.get_pending_gates(state.task_id)
            return state, f"Blocked by {len(pending)} pending approval(s)"

        try:
            new_state = state.transition_to(target)
            return new_state, None
        except ValueError as e:
            return state, str(e)
