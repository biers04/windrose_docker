# Windrose Dedicated Server on Linux

This project runs the current Windows-only Windrose dedicated-server files inside Docker on Linux by using Wine.

It is designed around the current public setup reality on April 15, 2026:

- The official Steam discussion and the bundled `DedicatedServer.md` describe a Windows server executable and JSON config flow.
- The dedicated server Steam app id is `4129620`.
- Anonymous Linux SteamCMD currently returned `Missing configuration` during validation on the target Ubuntu host, so this repo treats the Windows dedicated-server files as an input you provide.
- The container validates the Steam Tools root launcher `WindroseServer.exe`, but it runs the Unreal shipping binary `R5/Binaries/Win64/WindroseServer-Win64-Shipping.exe` directly under Wine for better stability in headless Docker.

Source used:
- Steam guide: https://steamcommunity.com/sharedfiles/filedetails/?id=3706337486
- Steam discussion: https://steamcommunity.com/app/3041230/discussions/0/807974232125489967/

## What this gives you

- A Docker image that can run the Windows dedicated server on Ubuntu.
- A clean project layout for one or more Windrose instances.
- Editable `ServerDescription.json` and `WorldDescription.json` files outside the runtime tree.
- Optional authenticated SteamCMD update checks on container boot.

## Project layout

```text
config/
  ServerDescription.json
  WorldDescription.json
logs/
runtime/
source/
steamcmd/
.env
compose.yaml
```

- `source/`: copy the Windows dedicated-server files here.
- `runtime/`: the container runs from this writable tree and refreshes it from `source/` on startup.
- `config/`: the JSON files you edit on the server. The container syncs admin-owned settings into the runtime tree on launch.
- `logs/`: container and Wine logs.
- `steamcmd/`: persisted SteamCMD home directory for authenticated update checks and cached login state.
- `.env`: optional Steam credentials and SteamCMD settings for automatic update checks.

## Getting the server files

Recommended source:

1. On a Windows machine with Steam, open Library.
2. Change the library filter to `Tools`.
3. Install `Windrose Dedicated Server`.
4. Copy or zip the installed folder and place its contents into `source/`.

This matches the official developer guidance and the bundled `DedicatedServer.md`.

Other options:

1. From an existing Windows host:
   Copy the full dedicated-server folder into `source/`.

2. SteamCMD with a licensed Steam account:
   The app metadata is public, but anonymous SteamCMD did not allow the actual depot download during testing on April 15, 2026. If you use SteamCMD here, use a real Steam account that has access to Windrose. This repo can run an authenticated SteamCMD update check on container boot.

3. Anonymous SteamCMD:
   Not reliable at the moment. Metadata works, but content download did not.

## Local run

```bash
cp compose.example.yaml compose.yaml
cp .env.example .env
docker compose build
docker compose up -d
docker compose logs -f
```

`docker compose build` downloads SteamCMD into the image automatically. You do not need to install SteamCMD separately on the host.

If the Windows server files are missing, the container exits with a clear message telling you which directory to populate.

## Quick start

If you just want the shortest path to a working test server on Linux:

1. Install the Linux-side requirements with the helper script.
2. Copy this repo to the Linux host.
3. Put the Steam Tools files into `./source/`.
4. Start the container.
5. Read the invite code.
6. Join from the game client with `Play -> Connect to Server`.

Recommended host bootstrap:

```bash
sudo ./scripts/install-host-requirements.sh
```

Example:

```bash
git clone https://github.com/biers04/windrose_docker.git windrose-dedicated
cd windrose-dedicated
sudo ./scripts/install-host-requirements.sh
cp .env.example .env
# Copy the contents of your Windows "Windrose Dedicated Server" install into ./source
docker compose build
docker compose up -d
docker compose logs -f
./scripts/show-invite-code.sh .
```

At that point:

- the server should be running in Docker
- `runtime/ServerDescription.json` should exist
- the invite code printed by `show-invite-code.sh` is what players use to join

If you later change settings in `config/ServerDescription.json` or `config/WorldDescription.json`, restart the container:

```bash
docker compose up -d --force-recreate
```

## Changing server settings

Edit these files on the Linux host:

- `config/ServerDescription.json`
- `config/WorldDescription.json`

For example:

```bash
nano config/ServerDescription.json
nano config/WorldDescription.json
```

After saving your changes, restart the container:

```bash
docker compose up -d --force-recreate
```

Then verify the server and invite code:

```bash
docker compose logs -f
./scripts/show-invite-code.sh .
```

## SteamCMD updates on boot

If you want the container to check Steam for updates every time it starts, copy the example environment file and set your Steam credentials:

```bash
cp .env.example .env
nano .env
```

Or use the helper:

```bash
./scripts/edit-steam-env.sh .
```

Example:

```dotenv
STEAM_UPDATE_ON_BOOT=true
STEAM_USERNAME=your-steam-account
STEAM_PASSWORD=your-steam-password
STEAMCMD_APP_ID=4129620
STEAMCMD_PLATFORM=windows
STEAMCMD_VALIDATE=false
```

How it works:

- On container start, the image runs an authenticated SteamCMD `app_update` against app `4129620`.
- The install target is `./source`, so Steam-managed server files stay outside the writable runtime tree.
- The container then `rsync`s `source/` into `runtime/` before launch so updated binaries are picked up on the same boot.
- SteamCMD state is persisted in `./steamcmd`, which lets cached login state survive reboots.

Important:

- Anonymous SteamCMD was not enough for Windrose during testing; use a real Steam account with access to the dedicated server tool.
- Storing a Steam password in `.env` is convenient but sensitive. Keep `.env` private.
- If Steam Guard blocks the first automated login, prime the SteamCMD state once and then future reboot checks can reuse the cached session.

One-time SteamCMD priming helper:

```bash
./scripts/prime-steamcmd.sh .
```

That opens SteamCMD inside the container with your persisted `./steamcmd` directory. If Steam prompts for Steam Guard on first login, complete that once there and then exit. After that, normal `docker compose up -d` boots can reuse the saved SteamCMD state.

## Editing the live server `.env`

For a real deployed instance, edit the instance `.env`, not the repo copy.

Example for the live Windrose test server used in this project:

```bash
nano /home/pve/windrose-servers/19/.env
```

Or with the helper:

```bash
/home/pve/windrose-dedicated/scripts/edit-steam-env.sh /home/pve/windrose-servers/19
```

Then set:

```dotenv
STEAM_UPDATE_ON_BOOT=true
STEAM_USERNAME=your-steam-account
STEAM_PASSWORD=your-steam-password
STEAMCMD_APP_ID=4129620
STEAMCMD_PLATFORM=windows
STEAMCMD_VALIDATE=false
```

After saving, restart the instance:

```bash
cd /home/pve/windrose-servers/19
docker compose up -d --force-recreate
```

## Networking and joining

Windrose currently uses invite-code joining, not direct IP or domain joins.

- Players join from the game client with `Play -> Connect to Server -> <invite code>`.
- The official guide describes ports as dynamically assigned through NAT punch-through / UPnP.
- Because of that, this repo uses `network_mode: host` and does not publish a fixed `ports:` list in Compose.
- In practice, there is no official fixed default game port to front in this setup today.

If the networking model changes in a future Windrose build and the developer documents stable game/query ports, you can replace host networking with explicit port publishing at that time.

## Invite code

There are two supported ways to get the invite code for a running server:

1. Watch the startup console logs.
2. Read `ServerDescription.json` after the server has started.

In this Docker layout, the recommended path is the helper script:

```bash
./scripts/show-invite-code.sh .
```

That script checks these files in order:

1. `runtime/R5/ServerDescription.json`
2. `runtime/ServerDescription.json`
3. `config/ServerDescription.json`

This matters because the live game runtime may update its own server description during startup, and that runtime file is the best source of truth for the currently active invite code.

If you want to read it manually, the most authoritative file is usually:

```bash
jq -r '.ServerDescription_Persistent.InviteCode' ./runtime/R5/ServerDescription.json
```

If the helper script does not return a value yet, check the logs:

```bash
docker compose logs -f
```

Windrose prints a `Server Connection Info` block when registration succeeds, and the invite code shown there is what players should use in `Play -> Connect to Server`.

## Config workflow

The guide identifies two important config files:

- `ServerDescription.json`
- `WorldDescription.json`

This project stores the admin-edited copies in `config/`. At container start:

1. `config/ServerDescription.json` is merged into the runtime server description.
2. `config/WorldDescription.json` is written into the selected saved world's versioned path.

On a brand new instance, Windrose creates its versioned RocksDB world directory during the first successful boot. That means world-setting changes are fully applied after the first startup has created a real path such as `R5/Saved/SaveProfiles/Default/RocksDB/0.10.0/Worlds/<world id>/WorldDescription.json`.

After first boot, the runtime-generated identity values are treated as authoritative. In practice, that means the sync script preserves or back-fills fields such as:

- `DeploymentId`
- `PersistentServerId`
- the selected real `WorldIslandId`

This avoids stale placeholder IDs from an initial config overwriting the real saved world on later restarts.

`P2pProxyAddress` is the host address Windrose advertises to its P2P/ICE networking layer. `0.0.0.0` is fine as a generic bind address, but it may not be enough for clients on the same LAN or nearby network path that need a concrete host address to reach. If `P2pProxyAddress` is left as `0.0.0.0`, the sync script attempts to auto-detect a usable host LAN IP and writes that into the runtime server description before launch.

The config files follow the official schema from the bundled `DedicatedServer.md`, including:

- `ServerDescription_Persistent`
- `WorldDescription`
- `WorldSettings.BoolParameters`
- `WorldSettings.FloatParameters`
- `WorldSettings.TagParameters`

## Host requirements

This repo includes a host bootstrap script:

```bash
sudo ./scripts/install-host-requirements.sh
```

It does these Linux-side setup steps for you:

- installs `docker.io`
- installs `docker-compose-v2`
- installs `unzip` and `jq`
- enables and starts Docker
- creates `source/`, `runtime/`, `config/`, and `logs/`
- creates `steamcmd/`
- creates `compose.yaml` from `compose.example.yaml` if needed
- copies `.env.example` to `.env` if needed

It does not download the actual Windrose dedicated-server files. Those still need to come from the official Steam Tools install on Windows.

## Importing a Windows zip on Linux

If you exported the Steam install as a zip from Windows:

```bash
unzip -q "Windrose Dedicated Server.zip" -d /tmp/windrose-import
mkdir -p ./source
cp -a /tmp/windrose-import/"Windrose Dedicated Server"/. ./source/
```

Expected root files include:

- `WindroseServer.exe`
- `DedicatedServer.md`
- `R5/Binaries/Win64/WindroseServer-Win64-Shipping.exe`

The root `WindroseServer.exe` acts like a small wrapper. In Docker, the image uses the shipping binary directly:

```text
R5/Binaries/Win64/WindroseServer-Win64-Shipping.exe -log
```

That keeps the runtime path closer to the successful manual Wine launch we validated on Ubuntu.

## Notes and limitations

- This is a compatibility workaround for a Windows-only dedicated server.
- It is not an officially supported Linux runtime from the game developer.
- Networking for Windrose appears to rely on NAT punch-through / UPnP according to the public guide, so the compose file uses `network_mode: host` on Linux instead of fixed published ports.
- You should keep the copied server files up to date with the game client version.
- GitHub's web UI sometimes briefly shows banners like `Cannot retrieve latest commit at this time` even when the repo and commits are fine. If the file tree is loading and `git clone` or `git fetch` still works, that is usually a transient GitHub-side web issue rather than a repo corruption issue.
