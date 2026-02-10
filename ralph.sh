#!/usr/bin/env bash
set -euo pipefail

RETRIES="${RETRIES:-10}"
MODEL="${MODEL:-gpt-5.3-codex}"
ROOT_DIR="${ROOT_DIR:-.}"

CODEX_ARGS=(exec --cd "$ROOT_DIR" --full-auto --model "$MODEL")

run_codex () {
  local task_file="$1"
  echo
  echo "== Task: ${task_file} =="
  echo
  codex "${CODEX_ARGS[@]}" "$(cat PROMPT.md)

$(cat "${task_file}")"
}

run_checks () {
  echo
  echo "== Local checks =="
  echo
  poetry run ruff check . || true
  poetry run ruff format . || true
  poetry run mypy . || true
  poetry run pytest -m smoke || true
}

iterate_task () {
  local task_file="$1"
  for i in $(seq 1 "$RETRIES"); do
    echo
    echo "---- Attempt $i/$RETRIES for ${task_file} ----"
    echo

    run_codex "$task_file"
    run_checks

    if git diff --quiet; then
      echo "No repo changes after this attempt."
      break
    fi
  done
}

if [[ "$#" -eq 0 ]]; then
  echo "Usage: RETRIES=10 ./ralph.sh TASK_03_REFACTOR.md [TASK_04_...md]"
  exit 1
fi

for task in "$@"; do
  iterate_task "$task"
done