#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
ENV_FILE="$SCRIPT_DIR/.env"

usage() {
  cat <<'EOF'
Usage: ./logs.sh [docker compose logs options]

Examples:
  ./logs.sh -f
  ./logs.sh --tail 100
  ./logs.sh -f --tail 100
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ ! -f "$ENV_FILE" ]]; then
  printf 'Error: missing environment file: %s\n' "$ENV_FILE" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
missing=()
for key in DEPLOY_HOST DEPLOY_USER DEPLOY_DIR; do
  [[ -n "${!key:-}" ]] || missing+=("$key")
done
if ((${#missing[@]})); then
  printf 'Error: .env is missing required values: %s\n' "${missing[*]}" >&2
  exit 1
fi

ssh -t "${DEPLOY_USER}@${DEPLOY_HOST}" "cd '$DEPLOY_DIR' && docker compose logs $(printf ' %q' "$@")"
