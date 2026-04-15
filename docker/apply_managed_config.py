#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import secrets
import shutil
from pathlib import Path


ROOT = Path("/srv/windrose")
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", ROOT / "config"))
RUNTIME_DIR = Path(os.getenv("RUNTIME_DIR", ROOT / "runtime"))
SERVER_PATH = CONFIG_DIR / "ServerDescription.json"
WORLD_PATH = CONFIG_DIR / "WorldDescription.json"
RUNTIME_SERVER_PATH = RUNTIME_DIR / "ServerDescription.json"
RUNTIME_R5_SERVER_PATH = RUNTIME_DIR / "R5" / "ServerDescription.json"


def _default_world_id() -> str:
    return secrets.token_hex(16).upper()


def _load_json(path: Path, fallback: dict) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fallback, indent=2) + "\n", encoding="utf-8")
    return fallback


server_doc = _load_json(
    SERVER_PATH,
    {
        "Version": 1,
        "DeploymentId": "",
        "ServerDescription_Persistent": {
            "PersistentServerId": "",
            "InviteCode": secrets.token_hex(4),
            "IsPasswordProtected": False,
            "Password": "",
            "ServerName": "Windrose Crew",
            "WorldIslandId": _default_world_id(),
            "MaxPlayerCount": 4,
            "P2pProxyAddress": "0.0.0.0",
        },
    },
)

if "ServerDescription_Persistent" not in server_doc and "ServerDescription" in server_doc:
    server_doc["ServerDescription_Persistent"] = server_doc.pop("ServerDescription")

server_desc = server_doc.setdefault("ServerDescription_Persistent", {})
world_id = str(server_desc.get("WorldIslandId") or _default_world_id()).strip().upper()
server_desc["WorldIslandId"] = world_id

world_doc = _load_json(
    WORLD_PATH,
    {
        "Version": 1,
        "WorldDescription": {
            "IslandId": world_id,
            "WorldName": server_desc.get("ServerName") or "Windrose Crew",
            "CreationTime": 0,
            "WorldPresetType": "Medium",
            "WorldSettings": {"BoolParameters": {}, "FloatParameters": {}, "TagParameters": {}},
        },
    },
)
world_desc = world_doc.setdefault("WorldDescription", {})
world_desc["IslandId"] = world_id
world_settings = world_desc.setdefault("WorldSettings", {})
for key in ("BoolParameters", "FloatParameters", "TagParameters"):
    if not isinstance(world_settings.get(key), dict):
        world_settings[key] = {}

RUNTIME_SERVER_PATH.write_text(json.dumps(server_doc, indent=2) + "\n", encoding="utf-8")

if RUNTIME_R5_SERVER_PATH.exists():
    try:
        runtime_r5_doc = json.loads(RUNTIME_R5_SERVER_PATH.read_text(encoding="utf-8"))
    except Exception:
        runtime_r5_doc = {}
    runtime_r5_doc["Version"] = server_doc.get("Version", 1)
    runtime_r5_doc["DeploymentId"] = runtime_r5_doc.get("DeploymentId") or server_doc.get("DeploymentId") or ""
    runtime_r5_desc = runtime_r5_doc.setdefault("ServerDescription_Persistent", {})
    runtime_r5_desc["PersistentServerId"] = runtime_r5_desc.get("PersistentServerId") or server_desc.get("PersistentServerId") or ""
    runtime_r5_desc["InviteCode"] = server_desc.get("InviteCode") or runtime_r5_desc.get("InviteCode") or ""
    runtime_r5_desc["IsPasswordProtected"] = bool(server_desc.get("IsPasswordProtected"))
    runtime_r5_desc["Password"] = server_desc.get("Password") or ""
    runtime_r5_desc["ServerName"] = server_desc.get("ServerName") or runtime_r5_desc.get("ServerName") or ""
    runtime_r5_desc["WorldIslandId"] = world_id
    runtime_r5_desc["MaxPlayerCount"] = int(server_desc.get("MaxPlayerCount") or runtime_r5_desc.get("MaxPlayerCount") or 4)
    runtime_r5_desc["P2pProxyAddress"] = server_desc.get("P2pProxyAddress") or runtime_r5_desc.get("P2pProxyAddress") or "0.0.0.0"
    RUNTIME_R5_SERVER_PATH.write_text(json.dumps(runtime_r5_doc, indent=2) + "\n", encoding="utf-8")

candidate_worlds = sorted(
    RUNTIME_DIR.glob("R5/Saved/SaveProfiles/Default/RocksDB/*/Worlds/*/WorldDescription.json")
)
if candidate_worlds:
    target_world = candidate_worlds[-1]
    target_world.parent.mkdir(parents=True, exist_ok=True)
    target_world.write_text(json.dumps(world_doc, indent=2) + "\n", encoding="utf-8")

managed_root = (
    RUNTIME_DIR
    / "R5"
    / "Saved"
    / "SaveProfiles"
    / "Default"
    / "RocksDB"
    / "managed"
)
if managed_root.exists():
    shutil.rmtree(managed_root)
