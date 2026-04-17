#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${SOURCE_DIR:-/srv/windrose/source}"
STEAM_STATE_DIR="${STEAM_STATE_DIR:-/srv/windrose/steamcmd}"
STEAMCMD_DIR="${STEAMCMD_DIR:-/opt/steamcmd}"
STEAMCMD_APP_ID="${STEAMCMD_APP_ID:-4129620}"
STEAMCMD_PLATFORM="${STEAMCMD_PLATFORM:-windows}"
STEAMCMD_VALIDATE="${STEAMCMD_VALIDATE:-false}"
STEAM_UPDATE_ON_BOOT="${STEAM_UPDATE_ON_BOOT:-false}"
STEAM_USERNAME="${STEAM_USERNAME:-}"
STEAM_PASSWORD="${STEAM_PASSWORD:-}"
SOURCE_EXECUTABLE="${WINDROSE_SOURCE_EXECUTABLE:-WindroseServer.exe}"

if [[ "$STEAM_UPDATE_ON_BOOT" != "1" && "${STEAM_UPDATE_ON_BOOT,,}" != "true" ]]; then
  exit 0
fi

if [[ -z "$STEAM_USERNAME" || -z "$STEAM_PASSWORD" ]]; then
  echo "SteamCMD update check skipped: set STEAM_USERNAME and STEAM_PASSWORD to enable authenticated updates." >&2
  exit 0
fi

if [[ ! -x "$STEAMCMD_DIR/steamcmd.sh" ]]; then
  echo "SteamCMD update check skipped: $STEAMCMD_DIR/steamcmd.sh was not found." >&2
  exit 0
fi

mkdir -p "$SOURCE_DIR" "$STEAM_STATE_DIR"
script_path="$(mktemp)"
trap 'rm -f "$script_path"' EXIT

validate_arg=""
if [[ "$STEAMCMD_VALIDATE" == "1" || "${STEAMCMD_VALIDATE,,}" == "true" ]]; then
  validate_arg=" validate"
fi

cat > "$script_path" <<EOF
@ShutdownOnFailedCommand 1
@NoPromptForPassword 1
@sSteamCmdForcePlatformType ${STEAMCMD_PLATFORM}
force_install_dir ${SOURCE_DIR}
login ${STEAM_USERNAME} ${STEAM_PASSWORD}
app_update ${STEAMCMD_APP_ID}${validate_arg}
quit
EOF

echo "Running SteamCMD update check for app ${STEAMCMD_APP_ID} into ${SOURCE_DIR}" >&2
if ! HOME="$STEAM_STATE_DIR" "$STEAMCMD_DIR/steamcmd.sh" +runscript "$script_path"; then
  if [[ -f "$SOURCE_DIR/$SOURCE_EXECUTABLE" ]]; then
    echo "SteamCMD update check failed, but existing Windrose files are present. Continuing with current source tree." >&2
    exit 0
  fi
  echo "SteamCMD update check failed and no existing Windrose source files are available." >&2
  exit 1
fi
