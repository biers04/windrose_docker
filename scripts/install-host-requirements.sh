#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this script with sudo or as root." >&2
  exit 1
fi

apt-get update
apt-get install -y docker.io docker-compose-v2 unzip jq
systemctl enable --now docker

install -d -m 755 \
  "$ROOT_DIR/source" \
  "$ROOT_DIR/runtime" \
  "$ROOT_DIR/config" \
  "$ROOT_DIR/logs"

if [[ ! -f "$ROOT_DIR/compose.yaml" ]]; then
  cp "$ROOT_DIR/compose.example.yaml" "$ROOT_DIR/compose.yaml"
fi

echo
echo "Host requirements installed."
echo "Next steps:"
echo "1. Copy the Windows Windrose Dedicated Server files into: $ROOT_DIR/source"
echo "2. Start the server:"
echo "   cd $ROOT_DIR && docker compose build && docker compose up -d"
echo "3. Read the invite code:"
echo "   cd $ROOT_DIR && ./scripts/show-invite-code.sh ."
