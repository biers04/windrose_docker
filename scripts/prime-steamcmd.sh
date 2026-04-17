#!/usr/bin/env bash
set -euo pipefail

INSTANCE_DIR="${1:-.}"

if [[ ! -f "$INSTANCE_DIR/compose.yaml" ]]; then
  echo "compose.yaml not found in $INSTANCE_DIR" >&2
  exit 1
fi

if [[ ! -f "$INSTANCE_DIR/.env" ]]; then
  echo ".env not found in $INSTANCE_DIR" >&2
  exit 1
fi

cd "$INSTANCE_DIR"
docker compose run --rm windrose bash -lc '
  export HOME="${STEAM_STATE_DIR:-/srv/windrose/steamcmd}"
  mkdir -p "$HOME"
  exec /opt/steamcmd/steamcmd.sh +force_install_dir /srv/windrose/source +login "$STEAM_USERNAME" "$STEAM_PASSWORD"
'
