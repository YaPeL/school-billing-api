#!/usr/bin/env bash
set -euo pipefail

RETRIES="${RETRIES:-10}"
MODEL="${MODEL:-gpt-5.3-codex}"
ROOT_DIR="${ROOT_DIR:-.}"

CODEX_ARGS=(exec --cd "$ROOT_DIR" --full-auto --model "$MODEL")

run_codex () {
  local task_file="$1"
  echo "== Starting Codex for ${task_file} =="
  codex "${CODEX_ARGS[@]}" "$(cat PROMPT.md)

$(cat "${task_file}")"
  echo "== Codex finished for ${task_file} =="
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

run_checks () {
  echo
  echo "== Local checks =="
  echo
  poetry run ruff check .
  poetry run ruff format .
  poetry run mypy .
  poetry run pytest -m smoke
}

iterate_task () {
  local task_file="$1"

  for i in $(seq 1 "$RETRIES"); do
    echo
    echo "---- Attempt $i/$RETRIES for ${task_file} ----"
    echo

    # Snapshot before
    local before
    before="$(git diff --stat)"

    run_codex "$task_file"

    # If nothing changed, stop retrying
    if git diff --quiet; then
      echo "No repo changes after this attempt."
      break
    fi

    # If the diff didn't change compared to previous attempt, stop retrying
    local after
    after="$(git diff --stat)"
    if [[ "$before" == "$after" ]]; then
      echo "No new changes compared to previous attempt."
      break
    fi

    # If checks pass, we're done with this task
    if run_checks; then
      echo "Checks passed. Task considered done."
      break
    else
      echo "Checks failed. Retrying..."
    fi
  done
}
