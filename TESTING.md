# Testing

## Backend

Run from the repository root:

```bash
python -m pip install -r backend/requirements-test.txt
pytest backend/tests --cov=app --cov-report=term-missing
python backend/scripts/generate_backend_test_reports.py
```

Reports:

- `backend/reports/tests/backend-tests.html`
- `backend/reports/tests/backend-tests.xml`
- `backend/reports/tests/backend-tests.txt`
- `backend/reports/coverage/index.html`

## Frontend

Run from `job-agent-frontend`:

```bash
npm install
npm run test
npm run test:coverage
npm run test:dom
npm run test:dom:coverage
npm run build
```

Notes:

- `npm run test` runs the Node/API suite from `src/test/node`
- `npm run test:coverage` builds API coverage for `src/api/**/*.js`
- `npm run test:dom` runs UI tests from `src/test/dom`
- `npm run build` is a production smoke check

If `vitest` fails with `ERR_MODULE_NOT_FOUND` for `vite`, reinstall frontend dependencies:

```bash
rm -rf node_modules package-lock.json
npm install
```
