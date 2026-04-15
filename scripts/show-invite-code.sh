#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
RUNTIME_R5_FILE="$ROOT_DIR/runtime/R5/ServerDescription.json"
RUNTIME_FILE="$ROOT_DIR/runtime/ServerDescription.json"
CONFIG_FILE="$ROOT_DIR/config/ServerDescription.json"

if [[ -f "$RUNTIME_R5_FILE" ]]; then
  jq -r '.ServerDescription_Persistent.InviteCode // empty' "$RUNTIME_R5_FILE"
  exit 0
fi

if [[ -f "$RUNTIME_FILE" ]]; then
  jq -r '.ServerDescription_Persistent.InviteCode // empty' "$RUNTIME_FILE"
  exit 0
fi

if [[ -f "$CONFIG_FILE" ]]; then
  jq -r '.ServerDescription_Persistent.InviteCode // empty' "$CONFIG_FILE"
  exit 0
fi

echo "No ServerDescription.json found under $ROOT_DIR/runtime/R5, $ROOT_DIR/runtime, or $ROOT_DIR/config" >&2
exit 1
