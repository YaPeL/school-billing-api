SHELL := /bin/bash

.PHONY: task review qa smoke fmt lint type

# Usage:
#   make task TASK=TASK_07_AUTH.md
#   make task TASK=TASK_06_ROUTES.md MODEL=gpt-5.3-codex
TASK ?=
MODEL ?= gpt-5.3-codex

task:
	@test -n "$(TASK)" || (echo "Missing TASK. Example: make task TASK=TASK_07_AUTH.md" && exit 1)
	codex exec --cd . --full-auto -c 'model="$(MODEL)"' "$$(cat PROMPT.md; echo; cat $(TASK))"

review:
	codex review --uncommitted

qa:
	poetry run ruff check .
	poetry run mypy .
	poetry run pytest -m smoke

smoke:
	poetry run pytest -m smoke

fmt:
	poetry run ruff format .

lint:
	poetry run ruff check .

type:
	poetry run mypy .
