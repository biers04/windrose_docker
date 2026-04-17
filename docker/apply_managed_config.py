#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import secrets
import shutil
import socket
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


def _load_existing_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _non_empty_string(value: object) -> str:
    return str(value or "").strip()


def _is_placeholder_world_id(value: object) -> bool:
    text = _non_empty_string(value).upper()
    return not text or text == "00000000000000000000000000000000"


def _is_placeholder_invite(value: object) -> bool:
    text = _non_empty_string(value)
    return not text or text.lower() == "changeme"


def _is_placeholder_p2p(value: object) -> bool:
    text = _non_empty_string(value)
    return not text or text == "0.0.0.0"


def _autodetect_local_ip() -> str:
    preferred = _non_empty_string(os.getenv("WINDROSE_P2P_PROXY_ADDRESS"))
    if preferred and preferred != "0.0.0.0":
        return preferred
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            detected = _non_empty_string(sock.getsockname()[0])
            if detected and detected != "0.0.0.0":
                return detected
    except OSError:
        pass
    try:
        detected = _non_empty_string(socket.gethostbyname(socket.gethostname()))
        if detected and detected != "127.0.0.1" and detected != "0.0.0.0":
            return detected
    except OSError:
        pass
    return "0.0.0.0"


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

runtime_r5_doc = _load_existing_json(RUNTIME_R5_SERVER_PATH)
runtime_r5_desc = runtime_r5_doc.get("ServerDescription_Persistent")
if not isinstance(runtime_r5_desc, dict):
    runtime_r5_desc = {}
runtime_server_doc = _load_existing_json(RUNTIME_SERVER_PATH)
runtime_server_desc = runtime_server_doc.get("ServerDescription_Persistent")
if not isinstance(runtime_server_desc, dict):
    runtime_server_desc = {}

server_desc = server_doc.setdefault("ServerDescription_Persistent", {})
runtime_world_id = _non_empty_string(runtime_r5_desc.get("WorldIslandId") or runtime_server_desc.get("WorldIslandId")).upper()
config_world_id = _non_empty_string(server_desc.get("WorldIslandId")).upper()
if _is_placeholder_world_id(config_world_id) and not _is_placeholder_world_id(runtime_world_id):
    world_id = runtime_world_id
else:
    world_id = config_world_id or _default_world_id()
server_desc["WorldIslandId"] = world_id
server_doc["Version"] = int(runtime_r5_doc.get("Version") or server_doc.get("Version") or 1)
server_doc["DeploymentId"] = _non_empty_string(runtime_r5_doc.get("DeploymentId") or runtime_server_doc.get("DeploymentId") or server_doc.get("DeploymentId"))
server_desc["PersistentServerId"] = _non_empty_string(
    runtime_r5_desc.get("PersistentServerId")
    or runtime_server_desc.get("PersistentServerId")
    or server_desc.get("PersistentServerId")
)
if _is_placeholder_invite(server_desc.get("InviteCode")):
    server_desc["InviteCode"] = _non_empty_string(
        runtime_r5_desc.get("InviteCode") or runtime_server_desc.get("InviteCode") or server_desc.get("InviteCode")
    ) or secrets.token_hex(4)
server_desc["ServerName"] = _non_empty_string(server_desc.get("ServerName") or runtime_r5_desc.get("ServerName") or "Windrose Crew")
server_desc["MaxPlayerCount"] = int(server_desc.get("MaxPlayerCount") or runtime_r5_desc.get("MaxPlayerCount") or 4)
server_desc["IsPasswordProtected"] = bool(server_desc.get("IsPasswordProtected"))
server_desc["Password"] = _non_empty_string(server_desc.get("Password"))
server_desc["P2pProxyAddress"] = (
    _autodetect_local_ip()
    if _is_placeholder_p2p(server_desc.get("P2pProxyAddress"))
    else _non_empty_string(server_desc.get("P2pProxyAddress"))
)

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
world_desc["WorldName"] = _non_empty_string(world_desc.get("WorldName") or server_desc.get("ServerName") or "Windrose Crew")
world_settings = world_desc.setdefault("WorldSettings", {})
for key in ("BoolParameters", "FloatParameters", "TagParameters"):
    if not isinstance(world_settings.get(key), dict):
        world_settings[key] = {}

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SERVER_PATH.write_text(json.dumps(server_doc, indent=2) + "\n", encoding="utf-8")
WORLD_PATH.write_text(json.dumps(world_doc, indent=2) + "\n", encoding="utf-8")
RUNTIME_SERVER_PATH.write_text(json.dumps(server_doc, indent=2) + "\n", encoding="utf-8")

if RUNTIME_R5_SERVER_PATH.exists():
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
    SERVER_PATH.write_text(json.dumps(runtime_r5_doc, indent=2) + "\n", encoding="utf-8")
    RUNTIME_SERVER_PATH.write_text(json.dumps(runtime_r5_doc, indent=2) + "\n", encoding="utf-8")

candidate_worlds = sorted(
    RUNTIME_DIR.glob("R5/Saved/SaveProfiles/Default/RocksDB/*/Worlds/*/WorldDescription.json")
)
target_world = None
for candidate in candidate_worlds:
    if candidate.parent.name.upper() == world_id:
        target_world = candidate
        break
if target_world:
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
