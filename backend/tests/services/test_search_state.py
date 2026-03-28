from __future__ import annotations

from app.services.search_state import (
    append_event,
    get_events_since,
    get_jobs,
    get_status_payload,
    mark_failed,
    mark_finished,
    mark_running,
)


def test_mark_running_resets_state():
    mark_running("user-1")
    append_event("user-1", "queued")
    mark_running("user-1")

    payload = get_status_payload("user-1")

    assert payload["status"] == "running"
    assert payload["jobs_found"] == 0
    assert payload["error"] is None
    assert payload["started_at"] is not None
    assert payload["finished_at"] is None


def test_mark_finished_updates_summary_and_jobs():
    jobs = [{"title": "Python Developer"}]
    summary = {
        "total_found": 7,
        "total_one_click": 3,
        "attempted_apply": 2,
        "applied_ok": 1,
        "error": None,
    }

    mark_finished("user-2", summary, jobs)

    payload = get_status_payload("user-2")
    assert payload["status"] == "finished"
    assert payload["jobs_found"] == 7
    assert payload["applications_sent"] == 1
    assert get_jobs("user-2") == jobs


def test_mark_failed_sets_error_and_finish_time():
    mark_running("user-3")
    mark_failed("user-3", "boom")

    payload = get_status_payload("user-3")

    assert payload["status"] == "failed"
    assert payload["error"] == "boom"
    assert payload["finished_at"] is not None


def test_append_event_keeps_only_last_500_entries():
    for index in range(505):
        append_event("user-4", f"event-{index}")

    events, offset = get_events_since("user-4", 0)

    assert len(events) == 500
    assert events[0]["message"] == "event-5"
    assert offset == 500


def test_get_events_since_respects_offset():
    append_event("user-5", "first")
    append_event("user-5", "second")

    events, offset = get_events_since("user-5", 1)

    assert [event["message"] for event in events] == ["second"]
    assert offset == 2
