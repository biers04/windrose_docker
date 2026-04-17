#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-}"
if [[ -z "$TARGET_DIR" ]]; then
  echo "usage: $0 /path/to/windrose-instance" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"/{config,logs,runtime,source,steamcmd}
cp compose.example.yaml "$TARGET_DIR/compose.yaml"
if [[ ! -f "$TARGET_DIR/.env" ]]; then
  cp .env.example "$TARGET_DIR/.env"
fi

cat > "$TARGET_DIR/config/ServerDescription.json" <<'EOF'
{
  "Version": 1,
  "DeploymentId": "",
  "ServerDescription_Persistent": {
    "PersistentServerId": "",
    "InviteCode": "changeme",
    "IsPasswordProtected": false,
    "Password": "",
    "ServerName": "Windrose Crew",
    "WorldIslandId": "00000000000000000000000000000000",
    "MaxPlayerCount": 4,
    "P2pProxyAddress": "0.0.0.0"
  }
}
EOF

cat > "$TARGET_DIR/config/WorldDescription.json" <<'EOF'
{
  "Version": 1,
  "WorldDescription": {
    "IslandId": "00000000000000000000000000000000",
    "WorldName": "Windrose Crew",
    "CreationTime": 0,
    "WorldPresetType": "Medium",
    "WorldSettings": {
      "BoolParameters": {},
      "FloatParameters": {},
      "TagParameters": {}
    }
  }
}
EOF

cat <<EOF
Initialized:
  $TARGET_DIR

Next:
  1. Copy the Windows dedicated-server files into $TARGET_DIR/source
  2. Optionally edit SteamCMD credentials in $TARGET_DIR/.env for update checks on boot
  3. Run the server once so Windrose creates its real runtime files
  4. Edit the JSON files in $TARGET_DIR/config
  5. Run: docker compose -f $TARGET_DIR/compose.yaml up -d --force-recreate
EOF
