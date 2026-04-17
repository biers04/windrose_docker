#!/usr/bin/env bash
set -euo pipefail

INSTANCE_DIR="${1:-.}"
ENV_PATH="$INSTANCE_DIR/.env"
EXAMPLE_PATH="$(dirname "$0")/../.env.example"

if [[ ! -f "$ENV_PATH" ]]; then
  if [[ -f "$EXAMPLE_PATH" ]]; then
    cp "$EXAMPLE_PATH" "$ENV_PATH"
  else
    cat > "$ENV_PATH" <<'EOF'
STEAM_UPDATE_ON_BOOT=false
STEAM_USERNAME=
STEAM_PASSWORD=
STEAMCMD_APP_ID=4129620
STEAMCMD_PLATFORM=windows
STEAMCMD_VALIDATE=false
EOF
  fi
fi

editor="${EDITOR:-nano}"
exec "$editor" "$ENV_PATH"
