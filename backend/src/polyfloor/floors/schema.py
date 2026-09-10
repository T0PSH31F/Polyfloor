"""Floor definition schema and runtime validator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError


class FloorDefinition(BaseModel):
    """Pydantic model validating floor configuration structure."""

    id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    email: Optional[str] = None
    org_name: str = Field(default="cyberia")
    timezone: str = Field(default="UTC")
    target_machine: Optional[str] = None
    db_schema: str = Field(..., min_length=1)
    mcps: list[str] = Field(default_factory=list)
    template: Optional[str] = None
    paid_models_allowed: bool = Field(default=False)
    daily_budget_usd: float = Field(default=0.0, ge=0.0)
    persist_paths: list[str] = Field(default_factory=list)
    config_json: dict[str, Any] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)


def validate_floor_dict(data: dict[str, Any]) -> FloorDefinition:
    """Validate a floor definition dictionary against FloorDefinition schema."""
    return FloorDefinition(**data)


def validate_floors_directory(directory: Path | str) -> list[FloorDefinition]:
    """Inspect and validate all JSON/YAML floor definition files in a directory.

    Fails loudly if any definition is malformed.
    """
    path = Path(directory)
    validated: list[FloorDefinition] = []
    if not path.exists() or not path.is_dir():
        return validated

    import json

    for item in path.glob("**/*"):
        if item.suffix in (".json", ".yaml", ".yml"):
            try:
                content = item.read_text(encoding="utf-8")
                if item.suffix == ".json":
                    raw = json.loads(content)
                else:
                    import yaml

                    raw = yaml.safe_load(content)
                if isinstance(raw, dict):
                    floor_def = validate_floor_dict(raw)
                    validated.append(floor_def)
            except Exception as e:
                raise ValueError(f"Malformed floor definition in file {item}: {e}") from e

    return validated
