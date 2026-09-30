#!/usr/bin/env python3
"""
Legacy boolean gate migration script.

Converts `human_approvals.<gate> = True` (legacy boolean) to proper
approval objects with identity, timestamp, and content hash per spec §6.1.

Usage:
    python -m tools.atw.migrate_gates --dry-run --thesis-id THESIS-2026-001
    python -m tools.atw.migrate_gates --write --thesis-id THESIS-2026-001
    python -m tools.atw.migrate_gates --dry-run --all
    python -m tools.atw.migrate_gates --write --all

Dry-run is default: outputs diff report without writing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add repo root to path for imports
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools.atw.approval import APPROVAL_GATES, GATE_KOSULLARI, icerik_ozeti
from tools.atw.state import (
    APPROVAL_GATES as STATE_APPROVAL_GATES,
    load_state,
    save_state,
    validate_state,
)

# Ensure both imports refer to the same list
assert APPROVAL_GATES == STATE_APPROVAL_GATES

MIGRATION_ID = str(uuid.uuid4())[:8]
LEGACY_APPROVED_BY = "system:legacy-migration"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _file_mtime_iso(path: Path) -> str:
    """Get file modification time as RFC 3339 string."""
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(timespec="seconds")


def migrate_thesis(
    thesis_path: Path,
    *,
    dry_run: bool = True,
    migration_id: str = MIGRATION_ID,
) -> dict[str, Any]:
    """
    Migrate a single thesis state file.

    Returns:
        dict with keys:
            - thesis_id: str
            - thesis_path: str
            - migrated_gates: list[str]
            - diff: list[dict] -- before/after per gate
            - validation_passed: bool
            - validation_errors: list[str] (empty if passed)
    """
    # Load current state
    try:
        state = load_state(thesis_path)
    except Exception as e:
        return {
            "thesis_id": thesis_path.stem,
            "thesis_path": str(thesis_path),
            "migrated_gates": [],
            "diff": [],
            "validation_passed": False,
            "validation_errors": [f"Failed to load state: {e}"],
        }

    thesis_id = state.get("thesis_id", thesis_path.stem)
    human_approvals = state.get("human_approvals", {})

    # Find legacy boolean True gates
    legacy_gates: list[str] = []
    for gate in APPROVAL_GATES:
        value = human_approvals.get(gate)
        if value is True:  # Legacy boolean True
            legacy_gates.append(gate)

    if not legacy_gates:
        return {
            "thesis_id": thesis_id,
            "thesis_path": str(thesis_path),
            "migrated_gates": [],
            "diff": [],
            "validation_passed": True,
            "validation_errors": [],
        }

    # Build diff report
    diff = []
    new_approvals = dict(human_approvals)

    for gate in legacy_gates:
        # Generate content hash from current state
        content_hash = icerik_ozeti(state, gate)

        # Use file mtime as approximation of when the approval happened
        approved_at = _file_mtime_iso(thesis_path)

        # New approval object per schema
        new_record = {
            "approved": True,
            "revision": 1,
            "approved_by": LEGACY_APPROVED_BY,
            "approved_at": approved_at,
            "content_hash": content_hash,
            "comment": None,
            "rejection_reason": None,
            "audit_refs": [],
        }

        diff.append({
            "gate": gate,
            "before": True,
            "after": new_record,
        })
        new_approvals[gate] = new_record

    # Create new state
    new_state = dict(state)
    new_state["human_approvals"] = new_approvals
    new_state["updated_at"] = _utc_now()

    # Validate against schema
    validation_errors = validate_state(new_state)
    validation_passed = len(validation_errors) == 0

    result = {
        "thesis_id": thesis_id,
        "thesis_path": str(thesis_path),
        "migrated_gates": legacy_gates,
        "diff": diff,
        "validation_passed": validation_passed,
        "validation_errors": validation_errors,
    }

    # Write if not dry-run and validation passes
    if not dry_run and validation_passed:
        save_state(thesis_path, new_state)

    return result


def find_thesis_files(root: Path) -> list[Path]:
    """Find all thesis_state.json files under root."""
    files = []
    for path in root.rglob("thesis_state.json"):
        # Skip if it's in a .git, __pycache__, schemas/, or similar
        parts = path.parts
        if any(part.startswith(".") or part in ("__pycache__", "schemas") for part in parts):
            continue
        files.append(path)
    return sorted(files)


def print_diff_report(results: list[dict[str, Any]], dry_run: bool) -> None:
    """Print human-readable diff report."""
    total_theses = len(results)
    total_migrated = sum(len(r["migrated_gates"]) for r in results)
    total_validation_fail = sum(1 for r in results if not r["validation_passed"])

    print(f"\n{'='*70}")
    print(f"MIGRATION REPORT ({'DRY-RUN' if dry_run else 'WRITE'})")
    print(f"{'='*70}")
    print(f"Migration ID: {MIGRATION_ID}")
    print(f"Legacy approver: {LEGACY_APPROVED_BY}")
    print(f"Theses scanned: {total_theses}")
    print(f"Gates migrated: {total_migrated}")
    print(f"Validation failures: {total_validation_fail}")
    print(f"{'='*70}\n")

    for r in results:
        thesis_id = r["thesis_id"]
        path = r["thesis_path"]
        migrated = r["migrated_gates"]
        passed = r["validation_passed"]
        errors = r["validation_errors"]

        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"Thesis: {thesis_id} ({status})")
        print(f"  Path: {path}")

        if not migrated:
            print(f"  No legacy gates found")
        else:
            print(f"  Migrated {len(migrated)} gate(s): {', '.join(migrated)}")
            for d in r["diff"]:
                gate = d["gate"]
                after = d["after"]
                print(f"    {gate}:")
                print(f"      before: true (legacy boolean)")
                print(f"      after:  approved={after['approved']}, "
                      f"revision={after['revision']}, "
                      f"approved_by={after['approved_by']!r}, "
                      f"approved_at={after['approved_at']}, "
                      f"content_hash={after['content_hash']}")

        if errors:
            print(f"  Validation errors:")
            for err in errors:
                print(f"    - {err}")

        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate legacy boolean approval gates to proper objects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run on specific thesis
  python -m tools.atw.migrate_gates --dry-run --thesis-id THESIS-2026-001

  # Write migration on specific thesis
  python -m tools.atw.migrate_gates --write --thesis-id THESIS-2026-001

  # Dry-run on all theses found
  python -m tools.atw.migrate_gates --dry-run --all

  # Write migration on all theses
  python -m tools.atw.migrate_gates --write --all
""",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--thesis-id",
        help="Specific thesis ID to migrate (looks for thesis_state.json in tezler/ or current dir)",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Migrate all thesis_state.json files found under tezler/ and current dir",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show what would be changed without writing (default)",
    )
    parser.add_argument(
        "--write",
        action="store_false",
        dest="dry_run",
        help="Actually write the migrated state to disk",
    )

    args = parser.parse_args()

    # Find thesis files
    thesis_files: list[Path] = []

    if args.thesis_id:
        # Look in common locations
        locations = [
            REPO_ROOT / "tezler" / args.thesis_id / "thesis_state.json",
            REPO_ROOT / args.thesis_id / "thesis_state.json",
            REPO_ROOT / "thesis_state.json",  # fallback
        ]
        for loc in locations:
            if loc.is_file():
                thesis_files.append(loc)
                break
        if not thesis_files:
            print(f"Error: thesis_state.json not found for thesis_id={args.thesis_id}", file=sys.stderr)
            print(f"  Searched: {[str(l) for l in locations]}", file=sys.stderr)
            return 1
    else:  # --all
        thesis_files = find_thesis_files(REPO_ROOT / "tezler")
        thesis_files += find_thesis_files(REPO_ROOT)
        # Deduplicate
        thesis_files = sorted(set(thesis_files), key=str)

    if not thesis_files:
        print("No thesis_state.json files found", file=sys.stderr)
        return 1

    print(f"Found {len(thesis_files)} thesis file(s)")
    for f in thesis_files:
        print(f"  {f}")

    # Run migration on each
    results = []
    for thesis_path in thesis_files:
        result = migrate_thesis(thesis_path, dry_run=args.dry_run)
        results.append(result)

    # Print report
    print_diff_report(results, args.dry_run)

    # Exit code: non-zero if any validation failed
    if any(not r["validation_passed"] for r in results):
        print("ERROR: Some theses failed validation after migration", file=sys.stderr)
        return 1

    if args.dry_run:
        print("DRY-RUN complete. Re-run with --write to apply changes.")
    else:
        print("Migration applied successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())