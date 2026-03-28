from __future__ import annotations

import sys

from app.tools import one_click_apply_tool, one_click_apply_wrapper, parser_crawler, parser_crawler_wrapper
from app.tools.parser_crawler import JobPosting


def test_fetch_html_returns_text(monkeypatch):
    class Response:
        text = "<html></html>"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(parser_crawler.session, "get", lambda url, params=None, timeout=10: Response())

    assert parser_crawler._fetch_html("https://example.com") == "<html></html>"


def test_fetch_html_handles_request_exception(monkeypatch):
    monkeypatch.setattr(
        parser_crawler.session,
        "get",
        lambda url, params=None, timeout=10: (_ for _ in ()).throw(parser_crawler.requests.RequestException("boom")),
    )

    assert parser_crawler._fetch_html("https://example.com") is None


def test_normalizers_cover_aliases_and_fallbacks():
    assert parser_crawler._normalize_specialization("Java Script") == "javascript"
    assert parser_crawler._normalize_specialization("Custom Stack") == "custom"
    assert parser_crawler._normalize_location(" Warszawa ") == "warszawa"
    assert parser_crawler._normalize_location(None) == "all-locations"
    assert parser_crawler._normalize_experience("jr") == "junior"
    assert parser_crawler._normalize_experience("manager") == "c-level"
    assert parser_crawler._normalize_experience(None) is None


def test_extract_job_title_from_list_text():
    assert parser_crawler._extract_job_title_from_list_text("Python Developer 10 000 PLN/month") == "Python Developer 10 000"
    assert parser_crawler._extract_job_title_from_list_text("") is None


def test_crawl_justjoin_parses_listing_html(monkeypatch):
    monkeypatch.setattr(
        parser_crawler,
        "_fetch_html",
        lambda url, params=None: """
            <html>
              <body>
                <a href="/job-offer/company-python-job">Python Developer 10 000 PLN/month 1-click Apply</a>
                <a href="/ignore">Ignore me</a>
              </body>
            </html>
        """,
    )

    jobs = parser_crawler.crawl_justjoin("python", "warszawa", "junior", 5)

    assert len(jobs) == 1
    assert jobs[0].url == "https://justjoin.it/job-offer/company-python-job"
    assert jobs[0].experience_level == "junior"


def test_search_jobs_handles_crawler_failure(monkeypatch):
    monkeypatch.setattr(
        parser_crawler,
        "crawl_justjoin",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    assert parser_crawler.search_jobs("python") == []


def test_search_jobs_tool_delegates_to_search_jobs(monkeypatch):
    monkeypatch.setattr(parser_crawler, "search_jobs", lambda **kwargs: ["ok"])

    assert parser_crawler.search_jobs_tool("python") == ["ok"]


def test_parser_crawler_cli_calls_search_jobs(monkeypatch, capsys):
    monkeypatch.setattr(
        parser_crawler.argparse.ArgumentParser,
        "parse_args",
        lambda self: type("Args", (), {"specialization": "python", "location": "warszawa", "experience": "junior", "limit": 3})(),
    )
    monkeypatch.setattr(parser_crawler, "search_jobs", lambda **kwargs: ["job"])

    parser_crawler._main_cli()
    captured = capsys.readouterr()

    assert "job" in captured.out


def test_parser_wrapper_validates_and_serializes(monkeypatch):
    monkeypatch.setattr(
        parser_crawler_wrapper,
        "search_jobs_tool",
        lambda **kwargs: [JobPosting(source="justjoin", url="https://example.com/job", title="Python Developer")],
    )

    result = parser_crawler_wrapper.justjoin_search_tool("python", limit=1)

    assert result == [{"source": "justjoin", "url": "https://example.com/job", "title": "Python Developer", "company": None, "location": None, "salary": None, "experience_level": None, "raw_snippet": None}]


def test_parser_wrapper_returns_empty_list_on_validation_error():
    assert parser_crawler_wrapper.justjoin_search_tool("", limit=0) == []


def test_parser_wrapper_returns_empty_list_on_runtime_error(monkeypatch):
    monkeypatch.setattr(
        parser_crawler_wrapper,
        "search_jobs_tool",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    assert parser_crawler_wrapper.justjoin_search_tool("python") == []


def test_one_click_filter_tool_filters_jobs():
    jobs = [
        JobPosting(source="justjoin", url="https://example.com/1", raw_snippet="1-click Apply"),
        JobPosting(source="justjoin", url="https://example.com/2", raw_snippet="redirect"),
    ]

    filtered = one_click_apply_tool.filter_one_click_apply(jobs)

    assert [job.url for job in filtered] == ["https://example.com/1"]
    assert one_click_apply_tool._has_one_click_apply(jobs[0]) is True
    assert one_click_apply_tool._has_one_click_apply(jobs[1]) is False


def test_one_click_filter_tool_handles_validation_and_runtime_errors(monkeypatch):
    assert one_click_apply_tool.one_click_apply_filter_tool([{"url": "missing-required-fields"}]) == []

    monkeypatch.setattr(
        one_click_apply_tool,
        "filter_one_click_apply",
        lambda jobs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    jobs = [{"source": "justjoin", "url": "https://example.com/1"}]
    assert one_click_apply_tool.one_click_apply_filter_tool(jobs) == []


def test_one_click_wrapper_returns_filtered_jobs(monkeypatch):
    monkeypatch.setattr(
        one_click_apply_wrapper,
        "one_click_apply_filter_tool",
        lambda jobs: [{"source": "justjoin", "url": "https://example.com/1"}],
    )

    jobs = [{"source": "justjoin", "url": "https://example.com/1"}]

    assert one_click_apply_wrapper.one_click_apply_wrapper_tool(jobs) == jobs


def test_one_click_wrapper_handles_errors(monkeypatch):
    assert one_click_apply_wrapper.one_click_apply_wrapper_tool([{"url": "broken"}]) == []

    monkeypatch.setattr(
        one_click_apply_wrapper,
        "one_click_apply_filter_tool",
        lambda jobs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    jobs = [{"source": "justjoin", "url": "https://example.com/1"}]
    assert one_click_apply_wrapper.one_click_apply_wrapper_tool(jobs) == []
