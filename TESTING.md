# Testing

## Backend

Run the full Python suite with coverage from the repository root:

```bash
pytest backend/tests --cov=app --cov-report=term-missing
```

Backend tests are grouped by theme under `backend/tests`:

- `api/routes`: route and handler tests
- `core`: security tests
- `repositories`: repository and dependency tests
- `services`: state, path, and runner tests
- `services/ai`: AI orchestration tests
- `tools`: crawler and apply wrapper tests

Generate HTML backend reports with:

```bash
python backend/scripts/generate_backend_test_reports.py
```

This writes:

- `backend/reports/tests/backend-tests.html`
- `backend/reports/tests/backend-tests.xml`
- `backend/reports/tests/backend-tests.txt`
- `backend/reports/coverage/index.html`

## Frontend API/Node Suite

Run the executable frontend suite from `job-agent-frontend`:

```bash
npm run test
npm run test:coverage
```

These tests run under `vitest.node.config.js` from `src/test/node`, grouped into:

- `node/api`: shared HTTP client and API wrappers
- `node/smoke`: import and smoke checks

## Frontend DOM Suite

A broader DOM-oriented suite is present in `job-agent-frontend/src/test/dom`, grouped into `app`, `components`, `contexts`, `pages`, and `router`:

```bash
npm run test:dom
npm run test:dom:coverage
```

In this environment, Vitest DOM workers did not start reliably, so the DOM suite is committed but was not part of the executed report below.

## Build Smoke Test

Verify the production frontend bundle:

```bash
cd job-agent-frontend
npm run build
```
