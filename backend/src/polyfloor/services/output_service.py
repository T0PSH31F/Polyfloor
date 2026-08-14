"""Filesystem output service — safe file writing for floor agents.

Validates paths to prevent traversal attacks and ensures agents can only
write within their designated floor output directory.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

# Floor ID must be alphanumeric with hyphens, 1-64 chars
FLOOR_ID_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{0,63}$")


class OutputError(Exception):
    """Raised when output path validation fails."""


class OutputService:
    """Manages safe filesystem outputs for floors."""

    def __init__(self, output_root: str = "/var/lib/polyfloor/floors"):
        self.output_root = Path(output_root).resolve()

    def validate_floor_id(self, floor_id: str) -> None:
        """Validate floor ID format."""
        if not FLOOR_ID_RE.match(floor_id):
            raise OutputError(
                f"Invalid floor ID '{floor_id}': must be lowercase alphanumeric with hyphens, 1-64 chars"
            )

    def get_floor_root(self, floor_id: str) -> Path:
        """Get the output root directory for a floor."""
        self.validate_floor_id(floor_id)
        return self.output_root / floor_id / "outputs"

    def validate_path(self, floor_id: str, relative_path: str) -> Path:
        """Validate and resolve a relative path within a floor's output directory.

        Prevents:
        - Path traversal (..)
        - Absolute paths
        - Symlink escapes
        - Writing outside the floor root

        Raises:
            OutputError: if the path is invalid or escapes the root
        """
        self.validate_floor_id(floor_id)

        # Reject absolute paths
        if os.path.isabs(relative_path):
            raise OutputError(f"Absolute paths are not allowed: '{relative_path}'")

        # Reject .. components
        if ".." in Path(relative_path).parts:
            raise OutputError(f"Path traversal not allowed: '{relative_path}'")

        floor_root = self.get_floor_root(floor_id)
        target = (floor_root / relative_path).resolve()

        # Ensure resolved path is under the floor root
        try:
            target.relative_to(floor_root)
        except ValueError:
            raise OutputError(
                f"Path '{relative_path}' escapes the floor output root"
            )

        return target

    def write_file(self, floor_id: str, relative_path: str, content: bytes, max_size: int = 10_485_760) -> Path:
        """Atomically write a file to a floor's output directory.

        Args:
            floor_id: The floor identifier
            relative_path: Path relative to the floor's output root
            content: File content as bytes
            max_size: Maximum allowed file size (default 10MB)

        Returns:
            The resolved path of the written file

        Raises:
            OutputError: if validation fails or write exceeds limits
        """
        if len(content) > max_size:
            raise OutputError(f"Content size {len(content)} exceeds maximum {max_size} bytes")

        target = self.validate_path(floor_id, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write via temp file + rename
        fd, tmp_path = tempfile.mkstemp(
            dir=target.parent,
            prefix=".polyfloor_tmp_",
        )
        try:
            os.write(fd, content)
            os.close(fd)
            os.rename(tmp_path, target)
        except Exception:
            os.close(fd) if not os.get_inheritable(fd) else None
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        return target

    def list_files(self, floor_id: str, relative_path: str = ".") -> list[str]:
        """List files in a floor's output directory."""
        target = self.validate_path(floor_id, relative_path)
        if not target.is_dir():
            return []
        return sorted(str(p.relative_to(self.get_floor_root(floor_id))) for p in target.iterdir())
