"""Task lifecycle transition validation tests."""

from __future__ import annotations

import pytest

from polyfloor.graph import TaskState, TaskStatus, WorkflowGraph


def test_valid_transitions():
    """All documented transitions should be valid."""
    test_cases = [
        ("backlog", "queued"),
        ("queued", "in_progress"),
        ("queued", "backlog"),
        ("in_progress", "staging"),
        ("in_progress", "rejected"),
        ("in_progress", "queued"),
        ("staging", "done"),
        ("staging", "rejected"),
        ("staging", "in_progress"),
        ("rejected", "backlog"),
        ("rejected", "queued"),
        ("done", "backlog"),
    ]

    for src, dst in test_cases:
        state = TaskState(task_id=1, floor_id="test", status=TaskStatus(src))
        assert state.can_transition_to(TaskStatus(dst)), f"{src} -> {dst} should be valid"


def test_invalid_transitions():
    """Transitions not in the map should be invalid."""
    invalid_cases = [
        ("backlog", "in_progress"),
        ("backlog", "done"),
        ("done", "staging"),
        ("rejected", "done"),
    ]

    for src, dst in invalid_cases:
        state = TaskState(task_id=1, floor_id="test", status=TaskStatus(src))
        assert not state.can_transition_to(TaskStatus(dst)), f"{src} -> {dst} should be invalid"


def test_transition_produces_new_state():
    state = TaskState(task_id=1, floor_id="test", status=TaskStatus.BACKLOG)
    new_state = state.transition_to(TaskStatus.QUEUED)
    assert new_state.status == TaskStatus.QUEUED
    assert state.status == TaskStatus.BACKLOG  # original unchanged


def test_invalid_transition_raises():
    state = TaskState(task_id=1, floor_id="test", status=TaskStatus.DONE)
    with pytest.raises(ValueError, match="Invalid transition"):
        state.transition_to(TaskStatus.STAGING)


def test_workflow_graph_approval_gate():
    graph = WorkflowGraph()
    state = TaskState(task_id=1, floor_id="test", status=TaskStatus.STAGING)

    from polyfloor.graph import ApprovalGate

    gate = ApprovalGate(
        approval_id=1, task_id=1, approval_type="publish", description="Publish blog"
    )
    graph.add_approval_gate(1, gate)

    assert not graph.can_proceed(1)
    new_state, error = graph.try_transition(state, TaskStatus.DONE, require_approval=True)
    assert error is not None
    assert "pending approval" in error

    graph.resolve_gate(1, 1, approved=True, resolved_by="admin")
    assert graph.can_proceed(1)
    new_state, error = graph.try_transition(state, TaskStatus.DONE, require_approval=True)
    assert error is None
    assert new_state.status == TaskStatus.DONE
