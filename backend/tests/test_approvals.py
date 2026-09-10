"""Approval resolution authorization tests."""

from __future__ import annotations

from polyfloor.auth import Principal, PrincipalRole


def test_worker_cannot_resolve_approvals():
    p = Principal(role=PrincipalRole.WORKER)
    assert not p.has_scope("approvals:resolve")


def test_readonly_cannot_resolve_approvals():
    p = Principal(role=PrincipalRole.READONLY)
    assert not p.has_scope("approvals:resolve")


def test_orchestrator_cannot_resolve_approvals():
    p = Principal(role=PrincipalRole.ORCHESTRATOR)
    assert not p.has_scope("approvals:resolve")


def test_hr_can_resolve_approvals():
    p = Principal(role=PrincipalRole.HR)
    assert p.has_scope("approvals:resolve")


def test_admin_can_resolve_approvals():
    p = Principal(role=PrincipalRole.HUMAN_ADMIN)
    assert p.has_scope("approvals:resolve")


def test_orchestrator_can_create_approvals():
    p = Principal(role=PrincipalRole.ORCHESTRATOR)
    assert p.has_scope("approvals:create")
