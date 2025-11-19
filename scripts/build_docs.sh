#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="$ROOT_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*[:=][[:space:]]*(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      value="${value%%#*}"
      value="${value%"${value##*[![:space:]]}"}"
      value="${value#"${value%%[![:space:]]*}"}"
      if [[ "$value" == \"*\" && "$value" == *\" && ${#value} -ge 2 ]]; then
        value="${value:1:-1}"
      elif [[ "$value" == \'*\' && "$value" == *\' && ${#value} -ge 2 ]]; then
        value="${value:1:-1}"
      fi
      export "$key=$value"
    fi
  done < "$ENV_FILE"
fi

PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x "$ROOT_DIR/venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT_DIR/venv/bin/python"
  elif [[ -x "$ROOT_DIR/venv/Scripts/python.exe" ]]; then
    PYTHON_BIN="$ROOT_DIR/venv/Scripts/python.exe"
  else
    PYTHON_BIN="$(command -v python3 || command -v python)"
  fi
fi

if [[ -z "$PYTHON_BIN" ]]; then
  echo "Не найден исполняемый файл Python. Установите Python или активируйте venv." >&2
  exit 1
fi

"$PYTHON_BIN" -m mkdocs build -f mkdocs.yml -d static/docs "$@"

