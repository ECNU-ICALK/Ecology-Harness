#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WITH_DEV=0
USE_UV=0

for arg in "$@"; do
  case "$arg" in
    --with-dev)
      WITH_DEV=1
      ;;
    --uv)
      USE_UV=1
      ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Usage: bash scripts/install.sh [--with-dev] [--uv]" >&2
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found in PATH." >&2
  exit 1
fi

python3 - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit("Python 3.9+ is required.")
PY

echo "==> Preparing Ecology Harness installation"
echo "    root: $ROOT_DIR"

if [[ "$USE_UV" -eq 1 ]]; then
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv was requested but is not installed." >&2
    exit 1
  fi
  echo "==> Installing with uv"
  if [[ "$WITH_DEV" -eq 1 ]]; then
    uv sync --directory "$ROOT_DIR" --extra dev
  else
    uv sync --directory "$ROOT_DIR"
  fi
else
  echo "==> Creating virtual environment"
  python3 -m venv "$ROOT_DIR/.venv"
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.venv/bin/activate"

  echo "==> Upgrading packaging tools"
  python3 -m pip install --upgrade pip setuptools wheel

  echo "==> Installing package"
  pushd "$ROOT_DIR" >/dev/null
  if [[ "$WITH_DEV" -eq 1 ]]; then
    python3 -m pip install -e '.[dev]'
  else
    python3 -m pip install -e .
  fi
  popd >/dev/null
fi

mkdir -p "$HOME/.ecology_harness/memory" "$HOME/.ecology_harness/skills" "$HOME/.ecology_harness/agents"

echo
echo "Ecology Harness is ready."
echo
echo "Next steps:"
if [[ "$USE_UV" -eq 1 ]]; then
  echo "  uv run --directory \"$ROOT_DIR\" eh --help"
  echo "  uv run --directory \"$ROOT_DIR\" eh -p '/tool Read {\"path\":\"README.md\"}'"
  echo "  uv run --directory \"$ROOT_DIR\" eh --repl"
else
  echo "  source \"$ROOT_DIR/.venv/bin/activate\""
  echo "  eh --help"
  echo "  eh -p '/tool Read {\"path\":\"README.md\"}'"
  echo "  eh --repl"
fi
