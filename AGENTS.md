# AGENTS.md

## Global (applies to all runs)
- Treat the user-provided prompt files (PROMPT.md, TASK_*.md) as the source of truth for what to do in this run.
- Follow repo conventions: FastAPI + SQLAlchemy 2.0 + PostgreSQL, Poetry, ruff/mypy, pytest markers (smoke/integration), and the Router -> Services -> DAL layering rules.
- Prefer small, safe diffs. Keep changes scoped to the requested task.

## Review mode guidelines (for codex review)
Act as a senior reviewer. Review uncommitted changes.

Priorities:
1) Correctness/edge cases
2) API design consistency (status codes, payloads, pagination)
3) Typing/mypy and test quality
4) Maintainability (DRY, naming, module boundaries)

Output format:
- Top 5 issues (most important first)
- Quick wins (small changes with high impact)
- Optional refactors (only if worth it)

Constraints:
- Do not propose large scope expansions.
- Do not suggest skipping tests.

Review strictness:
- Even if everything looks OK, still provide:
  - 2 potential risks/edge cases to double-check
  - 2 consistency checks (naming, status codes, pagination, typing)
  - 1 small improvement suggestion (if any), otherwise say "No changes recommended".
- If changes include tests, comment on test intent and what they do NOT cover.

## Run modes
- If running `codex exec`: produce code changes that satisfy the provided TASK_*.md.
- If running `codex review`: do not propose large refactors; focus on actionable findings.
