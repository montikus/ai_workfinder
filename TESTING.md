# Testing

## Backend

Run the full Python suite with coverage from the repository root:

```bash
pytest backend/tests --cov=app --cov-report=term-missing
```

This covers unit, service, tool-wrapper, and route-level backend tests.

## Frontend API/Node Suite

Run the executable frontend suite from `job-agent-frontend`:

```bash
npm run test
npm run test:coverage
```

These tests run under `vitest.node.config.js` and currently verify the shared HTTP client plus API wrapper modules.

## Frontend DOM Suite

A broader DOM-oriented suite is present in `job-agent-frontend/src/test`, including page, context, router, and component tests:

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
