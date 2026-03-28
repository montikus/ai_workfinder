from __future__ import annotations

import json

from app.tools import apply_http_tool, apply_http_wrapper


def test_file_error_validates_path(tmp_path):
    missing = apply_http_tool._file_error(str(tmp_path / "missing.pdf"))
    file_path = tmp_path / "resume.pdf"
    file_path.write_text("pdf", encoding="utf-8")

    assert "Resume file not found" in missing
    assert apply_http_tool._file_error(str(file_path)) is None
    assert "not a file" in apply_http_tool._file_error(str(tmp_path))


def test_offer_slug_and_api_url_helpers():
    assert apply_http_tool._offer_slug_from_job_url("https://justjoin.it/job-offer/python-role") == "python-role"
    assert apply_http_tool._offer_slug_from_job_url("https://api.justjoin.it/v1/offers/python-role/applications") == "python-role"
    assert apply_http_tool._build_api_url("https://justjoin.it/job-offer/python-role") == "https://api.justjoin.it/v1/offers/python-role/applications"


def test_apply_to_job_http_tool_returns_validation_error_for_bad_input():
    result = apply_http_tool.apply_to_job_http_tool(
        job_url="short",
        full_name="R",
        email="bad-email",
        resume_path="missing.pdf",
    )

    assert result["ok"] is False
    assert result["status_code"] == 0
    assert "validation:" in result["error"]


def test_apply_to_job_http_tool_returns_validation_error_for_missing_file():
    result = apply_http_tool.apply_to_job_http_tool(
        job_url="https://justjoin.it/job-offer/python-role",
        full_name="Roman Tester",
        email="user@example.com",
        resume_path="missing.pdf",
    )

    assert result["ok"] is False
    assert "Resume file not found" in result["error"]


def test_apply_to_job_http_tool_success_and_header_population(tmp_path):
    class Response:
        status_code = 201
        text = '{"id":"app-1"}'

        def json(self):
            return {"id": "app-1"}

    calls = []

    class Session:
        def post(self, api_url, headers, data, files, timeout):
            calls.append(
                {
                    "api_url": api_url,
                    "headers": headers,
                    "data": data,
                    "filename": files["attachment"][0],
                    "mime": files["attachment"][2],
                    "timeout": timeout,
                }
            )
            return Response()

    file_path = tmp_path / "resume.pdf"
    file_path.write_bytes(b"%PDF")

    result = apply_http_tool.apply_to_job_http_tool(
        job_url="https://justjoin.it/job-offer/python-role",
        full_name="Roman Tester",
        email="user@example.com",
        resume_path=str(file_path),
        x_identity="identity",
        recaptcha_token="captcha",
        session=Session(),
    )

    assert result["ok"] is True
    assert result["application_id"] == "app-1"
    assert calls[0]["headers"]["x-identity"] == "identity"
    assert calls[0]["headers"]["recaptcha-token"] == "captcha"
    assert calls[0]["filename"] == "resume.pdf"


def test_apply_to_job_http_tool_handles_http_error(tmp_path):
    class Response:
        status_code = 400
        text = "bad request"

        def json(self):
            return {"detail": "bad"}

    class Session:
        def post(self, *args, **kwargs):
            return Response()

    file_path = tmp_path / "resume.pdf"
    file_path.write_bytes(b"%PDF")

    result = apply_http_tool.apply_to_job_http_tool(
        job_url="https://justjoin.it/job-offer/python-role",
        full_name="Roman Tester",
        email="user@example.com",
        resume_path=str(file_path),
        session=Session(),
    )

    assert result["ok"] is False
    assert result["status_code"] == 400
    assert result["error"] == "http_error: 400"


def test_apply_to_job_http_tool_handles_request_exception(monkeypatch, tmp_path):
    class Session:
        def post(self, *args, **kwargs):
            raise apply_http_tool.requests.RequestException("network down")

    file_path = tmp_path / "resume.pdf"
    file_path.write_bytes(b"%PDF")

    result = apply_http_tool.apply_to_job_http_tool(
        job_url="https://justjoin.it/job-offer/python-role",
        full_name="Roman Tester",
        email="user@example.com",
        resume_path=str(file_path),
        session=Session(),
    )

    assert result["ok"] is False
    assert "request_exception" in result["error"]


def test_apply_http_wrapper_handles_validation_success_and_runtime_error(monkeypatch):
    invalid = apply_http_wrapper.apply_http_wrapper_tool(
        job_url="bad",
        full_name="R",
        email="bad",
        resume_path="missing.pdf",
    )
    assert invalid["ok"] is False

    monkeypatch.setattr(
        apply_http_wrapper,
        "apply_to_job_http_tool",
        lambda **kwargs: {"ok": True, "applied": True, "job_url": kwargs["job_url"]},
    )
    valid = apply_http_wrapper.apply_http_wrapper_tool(
        job_url="https://justjoin.it/job-offer/python-role",
        full_name="Roman Tester",
        email="user@example.com",
        resume_path="resume.pdf",
    )
    assert valid["ok"] is True

    monkeypatch.setattr(
        apply_http_wrapper,
        "apply_to_job_http_tool",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    runtime_error = apply_http_wrapper.apply_http_wrapper_tool(
        job_url="https://justjoin.it/job-offer/python-role",
        full_name="Roman Tester",
        email="user@example.com",
        resume_path="resume.pdf",
    )
    assert runtime_error["ok"] is False
    assert "runtime:" in runtime_error["error"]


def test_justjoin_apply_http_tool_returns_json(monkeypatch):
    monkeypatch.setattr(
        apply_http_wrapper,
        "apply_http_wrapper_tool",
        lambda **kwargs: {"ok": True, "applied": True, "job_url": kwargs["job_url"]},
    )

    tool = apply_http_wrapper.JustJoinApplyHttpTool()
    result = tool._run(
        job_url="https://justjoin.it/job-offer/python-role",
        full_name="Roman Tester",
        email="user@example.com",
        resume_path="resume.pdf",
    )

    assert json.loads(result)["ok"] is True
