"""Output path traversal prevention tests."""

from __future__ import annotations

import tempfile

import pytest

from polyfloor.services.output_service import OutputService, OutputError, FLOOR_ID_RE


@pytest.fixture
def output_service(tmp_path):
    return OutputService(output_root=str(tmp_path))


def test_valid_floor_ids():
    valid = ["production", "marketing", "dev", "customer-service", "floor-1", "a"]
    for fid in valid:
        assert FLOOR_ID_RE.match(fid), f"Expected valid: {fid}"


def test_invalid_floor_ids():
    invalid = ["", "Floor", "floor id", "../escape", "a" * 65, "-starts-dash"]
    for fid in invalid:
        assert not FLOOR_ID_RE.match(fid), f"Expected invalid: {fid}"


def test_reject_absolute_path(output_service):
    with pytest.raises(OutputError, match="Absolute"):
        output_service.validate_path("test-floor", "/etc/passwd")


def test_reject_traversal(output_service):
    with pytest.raises(OutputError, match="traversal"):
        output_service.validate_path("test-floor", "../../../etc/passwd")


def test_reject_encoded_traversal(output_service):
    with pytest.raises(OutputError, match="traversal"):
        output_service.validate_path("test-floor", "subdir/../../escape")


def test_accept_valid_path(output_service):
    path = output_service.validate_path("test-floor", "outputs/report.txt")
    assert "test-floor" in str(path)
    assert "report.txt" in str(path)


def test_invalid_floor_id(output_service):
    with pytest.raises(OutputError, match="Invalid floor ID"):
        output_service.validate_path("../evil", "file.txt")


def test_write_and_list(output_service):
    output_service.write_file("test-floor", "hello.txt", b"world")
    files = output_service.list_files("test-floor")
    assert "hello.txt" in files


def test_write_rejects_oversized(output_service):
    with pytest.raises(OutputError, match="exceeds maximum"):
        output_service.write_file("test-floor", "big.bin", b"x" * 20_000_000, max_size=10_000_000)
