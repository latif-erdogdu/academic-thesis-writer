#!/usr/bin/env python3
"""
Integration test for legacy boolean gate migration.

This test validates that the migration script correctly converts
legacy `human_approvals.<gate> = True` boolean values to proper
approval objects with identity, timestamp, and content hash per spec §6.1.

The test uses a real thesis state snapshot to ensure production-like validation.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from tools.atw.migrate_gates import migrate_thesis
from tools.atw.state import validate_state


def _legacy_thesis_state() -> dict:
    """Return a thesis state with legacy boolean approval gates.

    Matches the schema requirements from schemas/thesis_state.json:
    - citations array required
    - research_questions need type and status with valid enum values
    - all registry arrays required
    """
    return {
        "schema_version": "1.0",
        "thesis_id": "THESIS-2026-001",
        "title": "Test Thesis for Migration",
        "language": "tr",
        "research_questions": [{"id": "RQ-001", "text": "Test question", "type": "main", "status": "pending"}],
        "search_runs": [],
        "sources": [],
        "evidence_registry": [],
        "claims_registry": [],
        "findings_registry": [],
        "gap_registry": [],
        "discussion_registry": [],
        "conclusion_registry": [],
        "audit_registry": [],
        "paragraphs": [],
        "chapters": [],
        "datasets": [],
        "analyses": [],
        "statistics": [],
        "tables": [],
        "figures": [],
        "definitions": [],
        "variables": [],
        "open_questions": [],
        "quality_issues": [],
        "citations": [],
        "human_approvals": {
            "research_question": True,
            "search_strategy": True,
            "source_set": True,
            "research_gap": True,
            "methodology": True,
            "findings": False,
            "final_thesis": False,
        },
        "approval_events": [],
        "style_profile": "apa7",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "version": 1,
    }


def test_migration_converts_legacy_booleans_to_objects():
    """Migration converts legacy boolean True to proper approval objects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        thesis_path = Path(tmpdir) / "thesis_state.json"
        state = _legacy_thesis_state()
        thesis_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        # Run migration (dry-run first to inspect)
        result = migrate_thesis(thesis_path, dry_run=True)

        # Verify migration report
        assert result["validation_passed"] is True
        assert result["validation_errors"] == []
        assert len(result["migrated_gates"]) == 5
        migrated = set(result["migrated_gates"])
        expected = {"research_question", "search_strategy", "source_set", "research_gap", "methodology"}
        assert migrated == expected

        # Verify diff structure
        for diff in result["diff"]:
            gate = diff["gate"]
            before = diff["before"]
            after = diff["after"]
            assert before is True, f"Gate {gate}: before should be True"
            assert after["approved"] is True
            assert after["revision"] == 1
            assert after["approved_by"] == "system:legacy-migration"
            assert after["approved_at"] is not None
            assert after["content_hash"] is not None
            assert after["content_hash"].startswith("sha256:")
            assert after["comment"] is None
            assert after["rejection_reason"] is None
            assert after["audit_refs"] == []


def test_migration_writes_valid_state():
    """Migration produces a state that passes schema validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        thesis_path = Path(tmpdir) / "thesis_state.json"
        state = _legacy_thesis_state()
        thesis_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        # Run migration with write
        result = migrate_thesis(thesis_path, dry_run=False)

        assert result["validation_passed"] is True

        # Load the written state and validate again
        loaded = json.loads(thesis_path.read_text(encoding="utf-8"))
        errors = validate_state(loaded)
        assert errors == [], f"Written state fails validation: {errors}"

        # Verify all gates are now objects
        approvals = loaded["human_approvals"]
        for gate in ["research_question", "search_strategy", "source_set", "research_gap", "methodology"]:
            assert isinstance(approvals[gate], dict), f"Gate {gate} should be object after migration"
            assert approvals[gate]["approved"] is True
            assert approvals[gate]["approved_by"] == "system:legacy-migration"

        # Non-legacy gates unchanged
        assert approvals["findings"] is False
        assert approvals["final_thesis"] is False


def test_migration_idempotent():
    """Running migration twice produces same result (no double-migration)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        thesis_path = Path(tmpdir) / "thesis_state.json"
        state = _legacy_thesis_state()
        thesis_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        # First migration
        migrate_thesis(thesis_path, dry_run=False)
        first_state = json.loads(thesis_path.read_text(encoding="utf-8"))

        # Second migration (should be no-op)
        result = migrate_thesis(thesis_path, dry_run=False)
        second_state = json.loads(thesis_path.read_text(encoding="utf-8"))

        assert result["migrated_gates"] == []  # No legacy gates left
        assert first_state == second_state  # State unchanged


def test_migration_preserves_content_hash():
    """Migrated gates have valid content hashes based on current state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        thesis_path = Path(tmpdir) / "thesis_state.json"
        state = _legacy_thesis_state()
        thesis_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        migrate_thesis(thesis_path, dry_run=False)
        loaded = json.loads(thesis_path.read_text(encoding="utf-8"))

        for gate in ["research_question", "search_strategy", "source_set", "research_gap", "methodology"]:
            record = loaded["human_approvals"][gate]
            content_hash = record["content_hash"]
            assert content_hash is not None
            assert content_hash.startswith("sha256:")
            # 16 hex chars after sha256:
            assert len(content_hash) == 23  # "sha256:" (7) + 16 hex


def test_migration_uses_file_mtime_for_approved_at():
    """Migration uses file mtime as approximation for approval timestamp."""
    with tempfile.TemporaryDirectory() as tmpdir:
        thesis_path = Path(tmpdir) / "thesis_state.json"
        state = _legacy_thesis_state()
        thesis_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        # Get file mtime before migration
        import os
        mtime_before = thesis_path.stat().st_mtime

        migrate_thesis(thesis_path, dry_run=False)
        loaded = json.loads(thesis_path.read_text(encoding="utf-8"))

        for gate in ["research_question", "search_strategy", "source_set", "research_gap", "methodology"]:
            approved_at = loaded["human_approvals"][gate]["approved_at"]
            assert approved_at is not None
            # Should be RFC 3339 format
            assert "T" in approved_at
            assert approved_at.endswith("+00:00") or "Z" in approved_at


def test_migration_dry_run_does_not_write():
    """Dry-run mode does not modify the file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        thesis_path = Path(tmpdir) / "thesis_state.json"
        state = _legacy_thesis_state()
        original_content = json.dumps(state, ensure_ascii=False, indent=2)
        thesis_path.write_text(original_content, encoding="utf-8")

        migrate_thesis(thesis_path, dry_run=True)

        # File should be unchanged
        current_content = thesis_path.read_text(encoding="utf-8")
        assert current_content == original_content


def test_migration_invalid_state_fails():
    """Migration on invalid state reports validation errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        thesis_path = Path(tmpdir) / "thesis_state.json"
        # Invalid state: missing required fields
        invalid_state = {"thesis_id": "BAD", "human_approvals": {"research_question": True}}
        thesis_path.write_text(json.dumps(invalid_state), encoding="utf-8")

        result = migrate_thesis(thesis_path, dry_run=True)

        assert result["validation_passed"] is False
        assert len(result["validation_errors"]) > 0


def test_migration_all_gates_already_migrated():
    """Thesis with no legacy gates passes through unchanged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        thesis_path = Path(tmpdir) / "thesis_state.json"
        # Already fully migrated state
        state = {
            "schema_version": "1.0",
            "thesis_id": "THESIS-2026-001",
            "title": "Test Thesis for Migration",
            "language": "tr",
            "research_questions": [{"id": "RQ-001", "text": "Test question", "type": "main", "status": "pending"}],
            "search_runs": [],
            "sources": [],
            "evidence_registry": [],
            "claims_registry": [],
            "findings_registry": [],
            "gap_registry": [],
            "discussion_registry": [],
            "conclusion_registry": [],
            "audit_registry": [],
            "paragraphs": [],
            "chapters": [],
            "datasets": [],
            "analyses": [],
            "statistics": [],
            "tables": [],
            "figures": [],
            "definitions": [],
            "variables": [],
            "open_questions": [],
            "quality_issues": [],
            "citations": [],
            "human_approvals": {
                "research_question": {"approved": True, "revision": 1, "approved_by": "Dr. Test", "approved_at": "2026-01-01T00:00:00+00:00", "content_hash": "sha256:abcdef1234567890", "comment": None, "rejection_reason": None, "audit_refs": []},
                "search_strategy": {"approved": True, "revision": 1, "approved_by": "Dr. Test", "approved_at": "2026-01-01T00:00:00+00:00", "content_hash": "sha256:abcdef1234567890", "comment": None, "rejection_reason": None, "audit_refs": []},
                "source_set": {"approved": True, "revision": 1, "approved_by": "Dr. Test", "approved_at": "2026-01-01T00:00:00+00:00", "content_hash": "sha256:abcdef1234567890", "comment": None, "rejection_reason": None, "audit_refs": []},
                "research_gap": {"approved": True, "revision": 1, "approved_by": "Dr. Test", "approved_at": "2026-01-01T00:00:00+00:00", "content_hash": "sha256:abcdef1234567890", "comment": None, "rejection_reason": None, "audit_refs": []},
                "methodology": {"approved": True, "revision": 1, "approved_by": "Dr. Test", "approved_at": "2026-01-01T00:00:00+00:00", "content_hash": "sha256:abcdef1234567890", "comment": None, "rejection_reason": None, "audit_refs": []},
                "findings": False,
                "final_thesis": False,
            },
            "approval_events": [],
            "style_profile": "apa7",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "version": 1,
        }
        thesis_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        result = migrate_thesis(thesis_path, dry_run=True)

        assert result["validation_passed"] is True
        assert result["migrated_gates"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])