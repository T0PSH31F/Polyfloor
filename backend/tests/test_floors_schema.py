"""Tests for floor definition schema validation."""

from __future__ import annotations

import json
import pytest
from pydantic import ValidationError

from polyfloor.floors import FloorDefinition, validate_floor_dict, validate_floors_directory


def test_valid_floor_definition():
    data = {
        "id": "dev",
        "display_name": "Development Floor",
        "org_name": "cyberia",
        "timezone": "UTC",
        "db_schema": "tower_dev",
        "mcps": ["mcp-git", "mcp-nix"],
        "paid_models_allowed": False,
        "daily_budget_usd": 10.0,
        "persist_paths": ["/tmp/dev"],
    }
    floor_def = validate_floor_dict(data)
    assert floor_def.id == "dev"
    assert floor_def.display_name == "Development Floor"
    assert floor_def.paid_models_allowed is False


def test_invalid_floor_definition_missing_required():
    data = {
        "display_name": "Invalid Floor",
    }
    with pytest.raises(ValidationError):
        validate_floor_dict(data)


def test_validate_floors_directory(tmp_path):
    floors_dir = tmp_path / "floors"
    floors_dir.mkdir()

    valid_file = floors_dir / "valid.json"
    valid_file.write_text(
        json.dumps(
            {
                "id": "prod",
                "display_name": "Production",
                "db_schema": "tower_prod",
            }
        )
    )

    validated = validate_floors_directory(floors_dir)
    assert len(validated) == 1
    assert validated[0].id == "prod"


def test_validate_floors_directory_malformed_fails(tmp_path):
    floors_dir = tmp_path / "floors"
    floors_dir.mkdir()

    bad_file = floors_dir / "bad.json"
    bad_file.write_text("{malformed json")

    with pytest.raises(ValueError, match="Malformed floor definition"):
        validate_floors_directory(floors_dir)
