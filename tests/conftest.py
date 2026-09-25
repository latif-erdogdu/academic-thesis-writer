"""Ortak test yardimcilari."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "schemas"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def schema_dir() -> Path:
    return SCHEMA_DIR


@pytest.fixture(scope="session")
def fixture_dir() -> Path:
    return FIXTURE_DIR


def load_fixture(name: str) -> dict:
    """tests/fixtures/<name> dosyasini sozluk olarak yukler."""
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
