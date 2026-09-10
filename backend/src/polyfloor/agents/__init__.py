"""Agent executor interfaces and implementations.

Provides pluggable agent execution backends:
- CrewAIExecutor: optional, isolated behind feature flag
- OpenCodeExecutor: disabled by default, explicit opt-in

Never implements automatic publishing, spending, or arbitrary command execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskPacket:
    """Input packet for agent execution."""

    task_id: int
    floor_id: str
    role: str
    title: str
    description: str
    model_spec: str = "free://best-reasoning"
    max_tokens: int = 4096
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Output from agent execution."""

    success: bool
    output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class AgentExecutor(ABC):
    """Abstract base for agent executors."""

    @abstractmethod
    async def execute(self, packet: TaskPacket) -> ExecutionResult:
        """Execute a task and return the result."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this executor is available and configured."""
        ...


class NoopExecutor(AgentExecutor):
    """Default executor that does nothing — for testing and scaffolding."""

    async def execute(self, packet: TaskPacket) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            output=f"[noop] Task '{packet.title}' acknowledged but not executed (no agent backend configured)",
            metadata={"executor": "noop"},
        )

    def is_available(self) -> bool:
        return True


class CrewAIExecutor(AgentExecutor):
    """CrewAI-based agent executor.

    Isolated so it is not imported/instantiated during basic API startup.
    Requires `crewai` package and proper model configuration.
    """

    def __init__(self):
        self._crewai = None

    def is_available(self) -> bool:
        try:
            import crewai  # noqa: F401

            return True
        except ImportError:
            return False

    async def execute(self, packet: TaskPacket) -> ExecutionResult:
        if not self.is_available():
            return ExecutionResult(
                success=False,
                error="CrewAI is not installed. Install with: pip install 'polyfloor[agents]'",
            )

        # Lazy import to avoid import-time side effects
        try:
            from crewai import Agent, Crew, Task

            agent = Agent(
                role=packet.role,
                goal=f"Complete: {packet.title}",
                backstory=packet.description,
                verbose=False,
                allow_delegation=False,
            )

            task = Task(
                description=packet.description,
                expected_output="A completed task result",
                agent=agent,
            )

            crew = Crew(agents=[agent], tasks=[task], verbose=False)
            result = crew.kickoff()

            return ExecutionResult(
                success=True,
                output=str(result),
                metadata={"executor": "crewai"},
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"CrewAI execution failed: {e}",
            )


class OpenCodeExecutor(AgentExecutor):
    """OpenCode-based executor.

    Disabled by default. Requires explicit configuration and allow-listed
    working directory. Does NOT allow arbitrary shell execution.
    """

    def __init__(self, allowed_dirs: list[str] | None = None):
        self.allowed_dirs = allowed_dirs or []

    def is_available(self) -> bool:
        return len(self.allowed_dirs) > 0

    async def execute(self, packet: TaskPacket) -> ExecutionResult:
        if not self.is_available():
            return ExecutionResult(
                success=False,
                error="OpenCode executor is not configured. Set POLYFLOOR_OPENCODE_ALLOWED_DIRS to enable.",
            )

        return ExecutionResult(
            success=False,
            error="OpenCode executor is a placeholder — not yet implemented",
            metadata={"executor": "opencode", "status": "placeholder"},
        )


# Registry of available executors
_executor_registry: dict[str, AgentExecutor] = {
    "noop": NoopExecutor(),
}


def get_executor(name: str = "noop") -> AgentExecutor:
    """Get an executor by name."""
    return _executor_registry.get(name, _executor_registry["noop"])


def register_executor(name: str, executor: AgentExecutor):
    """Register an executor."""
    _executor_registry[name] = executor
