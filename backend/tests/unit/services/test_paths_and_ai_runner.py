from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import ai_runner
from app.services.ai.state import RunInput, summary_from_state
from app.services.paths import project_root, resume_path


def test_project_root_points_to_repository_root():
    root = project_root()

    assert (root / "pyproject.toml").exists()
    assert (root / "backend").exists()


def test_resume_path_uses_project_root(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.paths.project_root", lambda: tmp_path)

    result = resume_path("user-1", "resume.pdf")

    assert result == tmp_path / "backend" / "uploads" / "user-1" / "resume.pdf"


def test_run_ai_from_config_requires_api_credentials(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"specialization": "python", "full_name": "Roman", "email": "user@example.com", "resume_path": "resume.pdf"}), encoding="utf-8")

    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setattr(ai_runner, "project_root", lambda: tmp_path)

    with pytest.raises(RuntimeError, match="Missing OPENAI_BASE_URL / OPENAI_API_KEY"):
        ai_runner.run_ai_from_config(config_path)


def test_run_ai_from_config_requires_model(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "specialization": "python",
                "full_name": "Roman",
                "email": "user@example.com",
                "resume_path": "resume.pdf",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com")
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("OPENAI_MODEL", "")
    monkeypatch.setattr(ai_runner, "project_root", lambda: tmp_path)

    with pytest.raises(RuntimeError, match="Missing llm_model"):
        ai_runner.run_ai_from_config(config_path)


def test_run_ai_from_config_builds_graph_and_returns_summary(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "specialization": "python",
                "experience_level": "junior",
                "location": "Warsaw",
                "limit": 5,
                "full_name": "Roman",
                "email": "user@example.com",
                "resume_path": "resume.pdf",
                "llm_model": "gpt-test",
                "max_apply": 2,
            }
        ),
        encoding="utf-8",
    )

    class FakeGraph:
        def invoke(self, state):
            assert state["specialization"] == "python"
            return {
                **state,
                "phase": "done",
                "status": "done",
                "jobs": [{"title": "Python Developer"}],
                "one_click_jobs": [{"title": "Python Developer"}],
                "apply_results": [{"ok": True, "applied": True}],
            }

    llm_calls = []

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            llm_calls.append(kwargs)

    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com")
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setattr(ai_runner, "ChatOpenAI", FakeChatOpenAI)
    monkeypatch.setattr(ai_runner, "build_graph", lambda llm: FakeGraph())
    monkeypatch.setattr(ai_runner, "project_root", lambda: tmp_path)

    summary, state = ai_runner.run_ai_from_config(config_path)

    assert llm_calls[0]["model"] == "gpt-test"
    assert summary["ok"] is True
    assert summary["applied_ok"] == 1
    assert state["phase"] == "done"


def test_summary_from_state_counts_successful_applications():
    state = {
        "phase": "done",
        "status": "partial_done",
        "jobs": [{"id": 1}, {"id": 2}],
        "one_click_jobs": [{"id": 1}],
        "apply_results": [
            {"ok": True, "applied": True},
            {"ok": True, "applied": False},
            {"ok": False, "applied": False},
        ],
        "llm_trace": [{"agent": "supervisor"}],
    }

    summary = summary_from_state(state)

    assert summary.ok is True
    assert summary.total_found == 2
    assert summary.total_one_click == 1
    assert summary.attempted_apply == 3
    assert summary.applied_ok == 1


def test_run_input_to_state_conversion():
    state = ai_runner.state_from_input(
        RunInput(
            specialization="python",
            full_name="Roman",
            email="user@example.com",
            resume_path="resume.pdf",
        )
    )

    assert state["phase"] == "init"
    assert state["status"] == "running"
    assert state["jobs"] == []
