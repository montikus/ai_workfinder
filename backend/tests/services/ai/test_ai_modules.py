from __future__ import annotations

import json
import sys

import pytest

from app.services.ai import agents, graph_builder, main as ai_main, run_from_config


class DummyMessage:
    def __init__(self, content="ok"):
        self.content = content


class DummyLLM:
    def __init__(self, content="ok", raise_error=False):
        self.content = content
        self.raise_error = raise_error

    def invoke(self, messages):
        if self.raise_error:
            raise RuntimeError("llm down")
        return DummyMessage(self.content)


def test_supervisor_node_transitions_between_phases():
    supervisor = agents.make_supervisor_node(DummyLLM("next"))

    assert supervisor({"phase": "init"})["phase"] == "search"
    assert supervisor({"phase": "after_search"})["phase"] == "filter"
    assert supervisor({"phase": "after_filter", "one_click_jobs": []})["status"] == "done"
    assert supervisor({"phase": "after_apply", "apply_results": [{"ok": True, "applied": True}]})["status"] == "partial_done"
    assert supervisor({"phase": "search", "error": "boom"}) == {"phase": "done", "status": "error"}


def test_supervisor_router_maps_phase_to_next_node():
    assert agents.supervisor_router({"phase": "search"}) == "search"
    assert agents.supervisor_router({"phase": "filter"}) == "filter"
    assert agents.supervisor_router({"phase": "apply"}) == "apply"
    assert agents.supervisor_router({"phase": "done"}) == "done"


def test_search_agent_node_returns_jobs(monkeypatch):
    monkeypatch.setattr(
        agents,
        "justjoin_search_tool",
        lambda specialization, experience_level, location, limit: [{"title": "Python Developer"}],
    )

    node = agents.make_search_agent_node(DummyLLM("searching"))
    result = node({"specialization": "python", "experience_level": "junior", "location": "Warsaw", "limit": 5})

    assert result["phase"] == "after_search"
    assert result["jobs"] == [{"title": "Python Developer"}]


def test_search_agent_node_handles_failure(monkeypatch):
    monkeypatch.setattr(
        agents,
        "justjoin_search_tool",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("search broke")),
    )

    node = agents.make_search_agent_node(DummyLLM())
    result = node({"specialization": "python"})

    assert result["phase"] == "error"
    assert result["status"] == "error"
    assert "search_agent_failed" in result["error"]


def test_filter_agent_node_returns_one_click_jobs(monkeypatch):
    monkeypatch.setattr(
        agents,
        "one_click_apply_wrapper_tool",
        lambda jobs: [job for job in jobs if job.get("one_click")],
    )

    node = agents.make_one_click_filter_agent_node(DummyLLM())
    result = node({"jobs": [{"title": "A"}, {"title": "B", "one_click": True}]})

    assert result["phase"] == "after_filter"
    assert result["one_click_jobs"] == [{"title": "B", "one_click": True}]


def test_apply_agent_node_processes_jobs(monkeypatch):
    calls = []

    class DummySession:
        pass

    monkeypatch.setattr(agents.requests, "Session", DummySession)
    monkeypatch.setattr(
        agents,
        "apply_http_wrapper_tool",
        lambda **kwargs: calls.append(kwargs) or {"ok": True, "applied": True, "job_url": kwargs["job_url"]},
    )

    node = agents.make_apply_agent_node(DummyLLM())
    result = node(
        {
            "one_click_jobs": [{"url": "https://example.com/job-1"}],
            "full_name": "Roman",
            "email": "user@example.com",
            "resume_path": "resume.pdf",
            "timeout_sec": 12,
        }
    )

    assert result["phase"] == "after_apply"
    assert result["apply_results"] == [{"ok": True, "applied": True, "job_url": "https://example.com/job-1"}]
    assert calls[0]["timeout_sec"] == 12


def test_apply_agent_node_handles_missing_url(monkeypatch):
    monkeypatch.setattr(agents.requests, "Session", lambda: object())

    node = agents.make_apply_agent_node(DummyLLM())
    result = node(
        {
            "one_click_jobs": [{"title": "No URL"}],
            "full_name": "Roman",
            "email": "user@example.com",
            "resume_path": "resume.pdf",
        }
    )

    assert result["apply_results"][0]["error"] == "missing_url"


def test_apply_agent_node_handles_runtime_failure(monkeypatch):
    monkeypatch.setattr(agents.requests, "Session", lambda: object())
    monkeypatch.setattr(
        agents,
        "apply_http_wrapper_tool",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("apply broke")),
    )

    node = agents.make_apply_agent_node(DummyLLM())
    result = node(
        {
            "one_click_jobs": [{"url": "https://example.com/job-1"}],
            "full_name": "Roman",
            "email": "user@example.com",
            "resume_path": "resume.pdf",
        }
    )

    assert result["phase"] == "error"
    assert result["status"] == "error"
    assert "apply_agent_failed" in result["error"]


def test_build_graph_runs_full_pipeline(monkeypatch):
    monkeypatch.setattr(
        agents,
        "justjoin_search_tool",
        lambda **kwargs: [{"url": "https://example.com/job-1", "title": "Python Developer"}],
    )
    monkeypatch.setattr(
        agents,
        "one_click_apply_wrapper_tool",
        lambda jobs: jobs,
    )
    monkeypatch.setattr(
        agents.requests,
        "Session",
        lambda: object(),
    )
    monkeypatch.setattr(
        agents,
        "apply_http_wrapper_tool",
        lambda **kwargs: {"ok": True, "applied": True, "job_url": kwargs["job_url"]},
    )

    graph = graph_builder.build_graph(DummyLLM())
    final_state = graph.invoke(
        {
            "phase": "init",
            "status": "running",
            "specialization": "python",
            "experience_level": "junior",
            "location": "Warsaw",
            "limit": 3,
            "full_name": "Roman",
            "email": "user@example.com",
            "resume_path": "resume.pdf",
            "jobs": [],
            "one_click_jobs": [],
            "apply_results": [],
            "llm_trace": [],
        }
    )

    assert final_state["phase"] == "done"
    assert final_state["status"] == "partial_done"


def test_ai_main_requires_llm_config(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai-main",
            "--spec",
            "python",
            "--name",
            "Roman",
            "--email",
            "user@example.com",
            "--resume",
            "resume.pdf",
        ],
    )
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    with pytest.raises(SystemExit, match="Missing LLM config"):
        ai_main.main()


def test_ai_main_success_path(monkeypatch, capsys):
    class FakeGraph:
        def invoke(self, state):
            return {
                **state,
                "phase": "done",
                "status": "done",
                "jobs": [],
                "one_click_jobs": [],
                "apply_results": [],
                "llm_trace": [],
            }

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai-main",
            "--spec",
            "python",
            "--name",
            "Roman",
            "--email",
            "user@example.com",
            "--resume",
            "resume.pdf",
            "--llm-base-url",
            "https://example.com",
            "--llm-api-key",
            "secret",
            "--llm-model",
            "gpt-test",
        ],
    )
    monkeypatch.setattr(ai_main, "_build_llm", lambda *args, **kwargs: object())
    monkeypatch.setattr(ai_main, "build_graph", lambda llm: FakeGraph())

    exit_code = ai_main.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out)["status"] == "done"


def test_run_from_config_requires_existing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(run_from_config, "_project_root", lambda: tmp_path)
    monkeypatch.setenv("AI_WORKFINDER_CONFIG", str(tmp_path / "missing.json"))

    with pytest.raises(SystemExit, match="config.json not found"):
        run_from_config.main()


def test_run_from_config_success(monkeypatch, tmp_path, capsys):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "specialization": "python",
                "full_name": "Roman",
                "email": "user@example.com",
                "resume_path": "resume.pdf",
                "llm_model": "gpt-test",
            }
        ),
        encoding="utf-8",
    )

    class FakeGraph:
        def invoke(self, state):
            return {
                **state,
                "phase": "done",
                "status": "done",
                "jobs": [],
                "one_click_jobs": [],
                "apply_results": [],
                "llm_trace": [],
            }

    monkeypatch.setattr(run_from_config, "_project_root", lambda: tmp_path)
    monkeypatch.setenv("AI_WORKFINDER_CONFIG", str(config_path))
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com")
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setattr(run_from_config, "ChatOpenAI", lambda **kwargs: object())
    monkeypatch.setattr(run_from_config, "build_graph", lambda llm: FakeGraph())

    exit_code = run_from_config.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out)["status"] == "done"
