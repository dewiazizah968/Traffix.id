# Contributing to Traffix Backend

This backend is developed block-by-block so each pull request stays focused,
reviewable, and safe for demo readiness.

## Branch Naming

Use short, descriptive branch names:

- `feat/<scope>-<summary>` for new backend capabilities
- `fix/<scope>-<summary>` for bug fixes
- `chore/<scope>-<summary>` for maintenance and documentation
- `docs/<scope>-<summary>` for documentation-only work

Examples:

- `feat/api-v1-system-router`
- `feat/runtime-state-store`
- `chore/backend-pr-prep`

## Commit Naming

Use conventional commit style:

- `feat(scope): add new capability`
- `fix(scope): correct broken behavior`
- `chore(scope): update project maintenance files`
- `docs(scope): improve documentation`
- `test(scope): add or update tests`

Keep commits focused. A commit should explain one logical change.

## Pull Request Rules

- Keep PRs small enough to review in one sitting.
- Describe the user-facing or engineering outcome, not only file changes.
- Include test evidence in the PR description.
- Do not commit `.env`, model artifacts, scaler files, logs, or CSV datasets.
- Avoid unrelated refactors in feature PRs.
- Keep public API response contracts backward-compatible once consumed by the
  frontend.

## Coding Standards

- Python 3.11+.
- Follow PEP8 and Black-compatible formatting with max line length 88.
- Use FastAPI `APIRouter` for modular endpoints.
- Use Pydantic v2 models for request and response contracts.
- Use `pydantic-settings` for configuration; do not read `os.environ`
  directly in application modules.
- Use the standardized response helpers from `core/responses.py`.
- Raise `TraffixAPIException` for predictable API errors.
- Use domain loggers from `core/logger.py`.
- Add module-level docstrings to Python modules.
- Add Google-style docstrings to functions and classes.

## Testing Rules

Before opening a PR, run:

```bash
cd backend
python -m compileall -q app core ml sim rec weather scripts
```

For endpoint changes, validate with `TestClient` or a running dev server:

```bash
python scripts/run_dev.py
```

Then check:

- `GET /`
- `GET /health`
- `GET /api/v1/system/ping`
- `GET /api/v1/system/version`
- `GET /api/v1/system/status`

Every API response should include `success`, `request_id`, and `timestamp`.
Every HTTP response should include `X-Request-ID` and `X-Process-Time`.
