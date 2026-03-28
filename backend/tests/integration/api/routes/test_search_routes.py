from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.api.routes import search
from app.services.search_state import append_event, mark_failed, mark_finished, mark_running


def test_merge_jobs_enriches_application_results():
    merged = search._merge_jobs(
        [{"url": "https://example.com/1", "title": "Python Developer"}],
        [{"job_url": "https://example.com/1", "ok": True, "applied": True}],
    )

    assert merged[0]["apply_url"] == "https://example.com/1"
    assert merged[0]["applied"] is True
    assert merged[0]["application_status"] == "Applied"


def test_search_log_handler_filters_by_context(monkeypatch):
    events = []
    handler = search._SearchLogHandler("user-1")
    monkeypatch.setattr(search, "append_event", lambda user_id, message, level="INFO": events.append((user_id, message, level)))

    record = search.logging.LogRecord(
        name="ai.runner",
        level=20,
        pathname=__file__,
        lineno=10,
        msg="message",
        args=(),
        exc_info=None,
    )
    record_other = search.logging.LogRecord(
        name="random.module",
        level=20,
        pathname=__file__,
        lineno=11,
        msg="skip",
        args=(),
        exc_info=None,
    )

    token = search._current_search_user.set("user-1")
    try:
        handler.emit(record)
        handler.emit(record_other)
    finally:
        search._current_search_user.reset(token)

    assert events == [("user-1", "message", "INFO")]


def test_run_search_task_marks_finished(monkeypatch, user_document):
    user_id = str(user_document["_id"])
    config_path = Path("config.json")

    monkeypatch.setattr(
        search,
        "run_ai_from_config",
        lambda path: (
            {"apply_results": [{"job_url": "https://example.com/job", "ok": True, "applied": True}]},
            {"jobs": [{"url": "https://example.com/job", "title": "Python Developer"}]},
        ),
    )

    search._run_search_task(user_id, config_path)

    payload = search.get_status_payload(user_id)
    assert payload["status"] == "finished"
    assert search.get_jobs(user_id)[0]["application_status"] == "Applied"


def test_run_search_task_marks_failed(monkeypatch, user_document):
    user_id = str(user_document["_id"])
    monkeypatch.setattr(search, "run_ai_from_config", lambda path: (_ for _ in ()).throw(RuntimeError("boom")))

    search._run_search_task(user_id, Path("config.json"))

    payload = search.get_status_payload(user_id)
    assert payload["status"] == "failed"
    assert payload["error"] == "boom"


def test_start_search_requires_full_name(create_user):
    user = create_user(resume_filename="resume.pdf")

    with pytest.raises(HTTPException) as exc_info:
        search.start_search(
            search.SearchStartInput(specialization="python"),
            BackgroundTasks(),
            user,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Missing full name. Update your profile or provide it in the request."


def test_start_search_requires_resume(create_user):
    user = create_user(name="Roman")

    with pytest.raises(HTTPException) as exc_info:
        search.start_search(
            search.SearchStartInput(specialization="python"),
            BackgroundTasks(),
            user,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Resume not uploaded. Please upload your resume first."


def test_start_search_requires_existing_resume_file(
    create_user,
    monkeypatch,
    tmp_path,
):
    user = create_user(name="Roman", resume_filename="resume.pdf")
    monkeypatch.setattr(search, "resume_path", lambda user_id, filename: tmp_path / user_id / filename)

    with pytest.raises(HTTPException) as exc_info:
        search.start_search(
            search.SearchStartInput(specialization="python"),
            BackgroundTasks(),
            user,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Resume file not found on server. Please upload again."


def test_start_search_rejects_empty_specialization(
    create_user,
    monkeypatch,
    tmp_path,
):
    user = create_user(name="Roman", resume_filename="resume.pdf")
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"pdf")
    monkeypatch.setattr(search, "resume_path", lambda user_id, filename: resume)

    with pytest.raises(HTTPException) as exc_info:
        search.start_search(
            search.SearchStartInput(specialization="   "),
            BackgroundTasks(),
            user,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Specialization cannot be empty."


def test_start_search_rejects_parallel_run(
    create_user,
    monkeypatch,
    tmp_path,
):
    user = create_user(name="Roman", resume_filename="resume.pdf")
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"pdf")
    monkeypatch.setattr(search, "resume_path", lambda user_id, filename: resume)
    mark_running(str(user["_id"]))

    with pytest.raises(HTTPException) as exc_info:
        search.start_search(
            search.SearchStartInput(specialization="python"),
            BackgroundTasks(),
            user,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Search is already running."


def test_start_search_writes_config_and_queues_background_task(
    create_user,
    monkeypatch,
    tmp_path,
):
    user = create_user(name="Roman", resume_filename="resume.pdf")
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"pdf")
    config_path = tmp_path / "config.json"

    monkeypatch.setattr(search, "resume_path", lambda user_id, filename: resume)
    monkeypatch.setattr(search, "_config_path", lambda: config_path)
    background_tasks = BackgroundTasks()

    response = search.start_search(
        search.SearchStartInput(
            specialization="python",
            experience_level="junior",
            location="Warsaw",
            limit=10,
            max_apply=2,
            full_name="Roman Tester",
            user_request="remote only",
            llm_model="gpt-test",
            headless=False,
            timeout_sec=15,
            captcha_wait_sec=30,
            slow_mo_ms=25,
        ),
        background_tasks,
        user,
    )

    written = json.loads(config_path.read_text(encoding="utf-8"))

    assert response == {"status": "running"}
    assert len(background_tasks.tasks) == 1
    assert written["specialization"] == "python"
    assert written["resume_path"] == str(resume)
    assert written["llm_model"] == "gpt-test"


def test_search_status_and_jobs_return_state(user_document):
    mark_finished(
        str(user_document["_id"]),
        {"total_found": 3, "applied_ok": 1, "attempted_apply": 1, "total_one_click": 1},
        [{"title": "Python Developer"}],
    )

    status_response = search.search_status(user_document)
    jobs_response = search.list_jobs(user_document)

    assert status_response["status"] == "finished"
    assert jobs_response == [{"title": "Python Developer"}]


def test_search_stream_returns_logs_and_done_event(user_document, monkeypatch):
    user_id = str(user_document["_id"])
    mark_running(user_id)
    append_event(user_id, "AI search started")
    mark_finished(user_id, {"total_found": 1}, [{"title": "Python Developer"}])
    monkeypatch.setattr(search.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(search, "StreamingResponse", _fake_streaming_response)

    response = search.search_stream(user_document)
    body = "".join(response.iterator)

    assert response.media_type == "text/event-stream"
    assert "event: log" in body
    assert "AI search started" in body
    assert "event: status" in body
    assert "event: done" in body


def test_search_stream_handles_failed_state(user_document, monkeypatch):
    user_id = str(user_document["_id"])
    mark_running(user_id)
    mark_failed(user_id, "network error")
    monkeypatch.setattr(search.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(search, "StreamingResponse", _fake_streaming_response)

    response = search.search_stream(user_document)
    body = "".join(response.iterator)

    assert "network error" in body


class _FakeStreamingResponse:
    def __init__(self, iterator, media_type=None, headers=None):
        self.iterator = iterator
        self.media_type = media_type
        self.headers = headers or {}


def _fake_streaming_response(iterator, media_type=None, headers=None):
    return _FakeStreamingResponse(iterator, media_type=media_type, headers=headers)
