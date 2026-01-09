from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return current.parents[3]


def resume_path(user_id: str, filename: str) -> Path:
    root = project_root()
    return root / "backend" / "uploads" / user_id / filename
