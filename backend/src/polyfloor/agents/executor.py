"""Floor runner — creates task packets and invokes executors."""

from __future__ import annotations

from typing import Any

from ..services.model_router import ModelRouter
from . import ExecutionResult, TaskPacket, get_executor


class FloorRunner:
    """Orchestrates task execution through the model router and agent executor."""

    def __init__(
        self,
        model_router: ModelRouter,
        default_executor: str = "noop",
    ):
        self.model_router = model_router
        self.default_executor = default_executor

    async def run_task(
        self,
        floor_id: str,
        role: str,
        title: str,
        description: str,
        model_spec: str = "free://best-reasoning",
        max_tokens: int = 4096,
        context: dict[str, Any] | None = None,
        task_id: int = 0,
        executor_name: str | None = None,
    ) -> ExecutionResult:
        """Run a task through the agent execution pipeline.

        Args:
            floor_id: The floor this task belongs to
            role: The agent role (e.g., "orchestrator", "writer")
            title: Task title
            description: Task description
            model_spec: Model routing spec (e.g., "free://best-reasoning")
            max_tokens: Max tokens for the model call
            context: Additional context for the agent
            task_id: Database task ID
            executor_name: Override the default executor

        Returns:
            ExecutionResult with success/failure and output
        """
        # Validate model routing
        try:
            self.model_router.resolve(model_spec)
        except ValueError as e:
            return ExecutionResult(
                success=False,
                error=f"Model routing failed: {e}",
            )

        # Build task packet
        packet = TaskPacket(
            task_id=task_id,
            floor_id=floor_id,
            role=role,
            title=title,
            description=description,
            model_spec=model_spec,
            max_tokens=max_tokens,
            context=context or {},
        )

        # Get executor
        executor = get_executor(executor_name or self.default_executor)
        if not executor.is_available():
            return ExecutionResult(
                success=False,
                error=f"Executor '{executor_name or self.default_executor}' is not available",
            )

        # Execute
        return await executor.execute(packet)
