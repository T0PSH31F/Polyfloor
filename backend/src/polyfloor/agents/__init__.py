"""Agent execution package.

The MVP uses a mock control loop (see ``executor.py``) that walks the
digital-products pipeline one stage per action. Live model-backed execution
against the OpenAI-compatible router is a follow-on; the executor interface
here keeps that pluggable without committing to a heavy agent framework.
"""

from __future__ import annotations

from .executor import advance_task

__all__ = ["advance_task"]
