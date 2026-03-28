from __future__ import annotations

import html
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _suite_elements(root: ET.Element) -> list[ET.Element]:
    if root.tag == "testsuite":
        return [root]
    if root.tag == "testsuites":
        return root.findall("testsuite")
    return []


def _render_case(case: ET.Element) -> str:
    classname = case.attrib.get("classname", "")
    name = case.attrib.get("name", "")
    duration = case.attrib.get("time", "0")
    status = "passed"
    details = ""

    for node in case:
        if node.tag in {"failure", "error", "skipped"}:
            status = node.tag
            text = node.attrib.get("message") or (node.text or "")
            if text.strip():
                details = f"<pre>{html.escape(text.strip())}</pre>"
            break

    return (
        "<tr>"
        f"<td>{html.escape(classname)}</td>"
        f"<td>{html.escape(name)}</td>"
        f"<td>{html.escape(status)}</td>"
        f"<td>{html.escape(duration)}s</td>"
        f"<td>{details}</td>"
        "</tr>"
    )


def _write_html_report(xml_path: Path, html_path: Path, console_output: str) -> None:
    if not xml_path.exists():
        html_path.write_text(
            "<html><body><h1>Backend Test Report</h1><p>JUnit XML report was not generated.</p></body></html>",
            encoding="utf-8",
        )
        return

    root = ET.fromstring(xml_path.read_text(encoding="utf-8"))
    suites = _suite_elements(root)

    tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)
    duration = sum(float(suite.attrib.get("time", "0")) for suite in suites)

    rows = []
    for suite in suites:
        for case in suite.findall("testcase"):
            rows.append(_render_case(case))

    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Backend Test Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }}
    h1, h2 {{ margin-bottom: 12px; }}
    .summary {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; margin-bottom: 24px; }}
    .card {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 12px; background: #f9fafb; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    pre {{ white-space: pre-wrap; margin: 0; font-size: 12px; }}
    .links {{ margin: 16px 0; }}
  </style>
</head>
<body>
  <h1>Backend Test Report</h1>
  <div class="summary">
    <div class="card"><strong>Tests</strong><div>{tests}</div></div>
    <div class="card"><strong>Failures</strong><div>{failures}</div></div>
    <div class="card"><strong>Errors</strong><div>{errors}</div></div>
    <div class="card"><strong>Skipped</strong><div>{skipped}</div></div>
    <div class="card"><strong>Duration</strong><div>{duration:.2f}s</div></div>
  </div>
  <div class="links">
    <a href="../coverage/index.html">Open coverage HTML report</a>
  </div>
  <h2>Test Cases</h2>
  <table>
    <thead>
      <tr>
        <th>Class</th>
        <th>Test</th>
        <th>Status</th>
        <th>Duration</th>
        <th>Details</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  <h2>Console Output</h2>
  <pre>{html.escape(console_output)}</pre>
</body>
</html>
"""
    html_path.write_text(document, encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    reports_root = repo_root / "backend" / "reports"
    tests_root = reports_root / "tests"
    coverage_root = reports_root / "coverage"
    tests_root.mkdir(parents=True, exist_ok=True)
    coverage_root.mkdir(parents=True, exist_ok=True)

    junit_path = tests_root / "backend-tests.xml"
    html_path = tests_root / "backend-tests.html"
    console_path = tests_root / "backend-tests.txt"

    command = [
        sys.executable,
        "-m",
        "pytest",
        "backend/tests",
        "--cov=app",
        "--cov-report=term-missing",
        f"--cov-report=html:{coverage_root}",
        f"--junitxml={junit_path}",
    ]
    result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)

    console_output = result.stdout
    if result.stderr:
        console_output = f"{console_output}\n{result.stderr}".strip()

    console_path.write_text(console_output, encoding="utf-8")
    _write_html_report(junit_path, html_path, console_output)

    print(f"HTML test report: {html_path}")
    print(f"Coverage report: {coverage_root / 'index.html'}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
