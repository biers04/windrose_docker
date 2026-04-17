#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${SOURCE_DIR:-/srv/windrose/source}"
RUNTIME_DIR="${RUNTIME_DIR:-/srv/windrose/runtime}"
CONFIG_DIR="${CONFIG_DIR:-/srv/windrose/config}"
LOG_DIR="${LOG_DIR:-/srv/windrose/logs}"
STEAM_STATE_DIR="${STEAM_STATE_DIR:-/srv/windrose/steamcmd}"
SOURCE_EXECUTABLE="${WINDROSE_SOURCE_EXECUTABLE:-WindroseServer.exe}"
EXECUTABLE="${WINDROSE_EXECUTABLE:-R5/Binaries/Win64/WindroseServer-Win64-Shipping.exe}"
WINE_COMMAND="${WINDROSE_WINE_COMMAND:-wine}"

mkdir -p "$SOURCE_DIR" "$RUNTIME_DIR" "$CONFIG_DIR" "$LOG_DIR" "$STEAM_STATE_DIR"

/usr/local/bin/update-source.sh

if [[ ! -f "$SOURCE_DIR/$SOURCE_EXECUTABLE" ]]; then
  cat <<EOF
Windrose dedicated-server files were not found.

Expected:
  $SOURCE_DIR/$SOURCE_EXECUTABLE

Copy the Windows dedicated-server files into the mounted source directory,
then restart the container.
EOF
  exit 1
fi

if [[ ! -f "$SOURCE_DIR/$EXECUTABLE" ]]; then
  cat <<EOF
Windrose dedicated-server binary was not found.

Expected:
  $SOURCE_DIR/$EXECUTABLE

The source directory appears incomplete. Re-copy the full Steam Tools install
contents into the mounted source directory, then restart the container.
EOF
  exit 1
fi

rsync -a "$SOURCE_DIR"/ "$RUNTIME_DIR"/

if [[ ! -d "$WINEPREFIX" ]]; then
  mkdir -p "$WINEPREFIX"
fi

cd "$RUNTIME_DIR"
export WINEPREFIX WINEARCH DISPLAY WINE_COMMAND EXECUTABLE
exec xvfb-run -a bash -lc '
  set -euo pipefail
  wineboot -u >/dev/null 2>&1 || true
  python3 /usr/local/bin/apply_managed_config.py

  "$WINE_COMMAND" "$EXECUTABLE" &
  server_pid=$!
  trap "kill $server_pid 2>/dev/null || true" INT TERM

  for _ in $(seq 1 60); do
    if [[ -f /srv/windrose/runtime/R5/ServerDescription.json ]]; then
      python3 /usr/local/bin/apply_managed_config.py || true
      break
    fi
    if ! kill -0 "$server_pid" 2>/dev/null; then
      break
    fi
    sleep 2
  done

  wait "$server_pid"
'
