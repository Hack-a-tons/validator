#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
ENV_FILE="$SCRIPT_DIR/.env"

usage() {
  cat <<'EOF'
Usage: ./deploy.sh [-m "COMMIT_MESSAGE"]

Deploy the current git branch to the configured server.
  -m MESSAGE  Commit all current changes and push before deploying.
  -h, --help  Show this help message.
EOF
}

validate_env() {
  local required=(DEPLOY_HOST DEPLOY_USER DEPLOY_DIR PORT OPENAI_API_KEY TWELVELABS_API_KEY)
  local missing=() key
  if [[ ! -f "$ENV_FILE" ]]; then
    printf 'Error: missing environment file: %s\n' "$ENV_FILE" >&2
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  for key in "${required[@]}"; do
    [[ -n "${!key:-}" ]] || missing+=("$key")
  done
  if ((${#missing[@]})); then
    printf 'Error: .env is missing required values: %s\n' "${missing[*]}" >&2
    exit 1
  fi
}

commit_message=""
while (($#)); do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -m)
      [[ $# -ge 2 ]] || { printf '%s\n' 'Error: -m requires a commit message.' >&2; exit 2; }
      commit_message="$2"; shift 2 ;;
    *) printf 'Error: unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

validate_env
cd "$SCRIPT_DIR"

if [[ -n "$commit_message" ]]; then
  git add .
  git commit -m "$commit_message"
  git push
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
remote="${DEPLOY_USER}@${DEPLOY_HOST}"
remote_branch="$(ssh "$remote" "cd '$DEPLOY_DIR' && git rev-parse --abbrev-ref HEAD")"
if [[ "$remote_branch" != "$branch" ]]; then
  printf 'Error: remote branch is %s; local branch is %s. Switch the remote branch first.\n' "$remote_branch" "$branch" >&2
  exit 1
fi

ssh "$remote" "cd '$DEPLOY_DIR' && git pull origin '$branch'"
local_env_hash="$(md5sum "$ENV_FILE" | awk '{print $1}')"
remote_env_hash="$(ssh "$remote" "test -f '$DEPLOY_DIR/.env' && md5sum '$DEPLOY_DIR/.env' | awk '{print \$1}'" || true)"
if [[ "$local_env_hash" != "$remote_env_hash" ]]; then
  scp "$ENV_FILE" "$remote:$DEPLOY_DIR/.env"
fi
ssh "$remote" "cd '$DEPLOY_DIR' && docker compose up -d --build --remove-orphans"
