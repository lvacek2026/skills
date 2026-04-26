---
name: iotstack-install
description: Expert on installing a complete IOTstack (Docker, Mosquitto, Node-RED, n8n, InfluxDB 1.x/2.x, Grafana, Portainer, Homebridge) on Debian/Raspberry Pi servers including aliases, Tailscale tunnel, PiBuilder workflow, and optimizations. Use when the user wants to install an IOT stack on a new server.
argument-hint: "[ssh-command]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
user-invocable: true
effort: high
---

# IOTstack Installation Expert

You are an expert on installing IOTstack (https://github.com/SensorsIot/IOTstack) on Debian and Raspberry Pi servers. Proceed systematically and verify every step.

## Input Parameters

- `$ARGUMENTS` — SSH command to connect to the server (e.g. `ssh -i key/id_ed25519 user@host`)

If no parameters are provided, ask the user for SSH access details.

## Installation Process

### Phase 0: Detect existing PiBuilder installation (Raspberry Pi)

If the Pi was deployed via [PiBuilder](https://github.com/Paraphraser/PiBuilder), much is already done. **Always check first:**

```bash
ls /home/pi/IOTstack 2>/dev/null && echo "IOTstack repo present"
ls /home/pi/PiBuilder 2>/dev/null && echo "PiBuilder workflow used"
ls /home/pi/.local/IOTstackAliases/ 2>/dev/null && echo "Aliases installed for pi"
which mc && echo "Midnight Commander OK"
ls /etc/argon/ 2>/dev/null && echo "Argon ONE fan controller scripts OK"
sudo systemctl is-active argononed
sudo systemctl list-jobs --no-pager | grep -E "userconfig|multi-user"
```

**If PiBuilder workflow was used:**
- IOTstack repo lives in `/home/pi/IOTstack` (owned by `pi`, not the current user)
- Aliases are per-user for `pi` (`~pi/.bashrc` sources `~/.local/IOTstackAliases/dot_iotstack_aliases`)
- `mc`, NTP, Samba, IOTstackBackup, Argon ONE scripts are already installed
- Docker is already installed and active
- `.env` may have a default `TZ=Europe/London` — verify and fix per the user's timezone
- **SKIP Phases 3, 4, 5, 7** — go straight to Phase 6 (service configuration)
- Do IOTstack work as `pi`: `sudo -u pi -i` or `ssh pi@…`

**Common blockers after PiBuilder:**
- `userconfig.service` (RPi imager first-boot wizard) may hang on `/dev/tty8` and block `multi-user.target` → `argononed` waits in queue as `inactive (dead)`. Fix:
  ```bash
  sudo systemctl disable --now userconfig.service
  sudo systemctl list-jobs --no-pager | awk '/userconfig|cloud-final|cloud-init/ {print $1}' | xargs -rI{} sudo systemctl cancel {}
  ```
- After fix: `sudo systemctl status argononed` should show `active (running)`.

### Phase 1: Server Reconnaissance

Connect to the server and gather:

```bash
echo "=== OS ===" && cat /etc/os-release | head -5
echo "=== Arch ===" && uname -m
echo "=== Kernel ===" && uname -r
echo "=== CPU ===" && nproc
echo "=== RAM ===" && free -h | head -2
echo "=== Disk ===" && df -h /
echo "=== User ===" && id
echo "=== Sudo ===" && sudo -l 2>&1 | tail -5
echo "=== Docker ===" && docker --version 2>/dev/null || echo "Not installed"
echo "=== Docker Compose ===" && docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || echo "Not installed"
```

**Verify:**
- Minimum disk: 3 GB free for the basic stack, 8 GB+ for the full stack (with InfluxDB, Grafana, n8n)
- Minimum RAM: 2 GB (4 GB+ recommended for the full stack)
- Sudo access — note any restrictions (some servers block usermod/useradd)
- OS compatibility — Debian 11+, Raspberry Pi OS, Ubuntu 20.04+

**Inform the user about server state and recommend a stack scope based on resources:**
- < 3 GB disk: Mosquitto + Portainer only
- 3-5 GB disk: Mosquitto + Node-RED + Portainer
- 5-10 GB disk: + n8n OR (InfluxDB + Grafana)
- 10 GB+ disk: full stack

### Phase 2: Service Selection

**IMPORTANT: ALWAYS ask the user which services to install before proceeding.**

Show the user a clear table of available services with descriptions and approximate Docker image sizes:

| # | Service | Description | Image ~size | Port |
|---|--------|-------|-----------------|------|
| 1 | **Mosquitto** | MQTT broker — mediates communication between IoT devices (sensors, actuators). Lightweight, reliable, the foundation of any IoT stack. | ~10 MB | 1883 |
| 2 | **Node-RED** | Visual flow-based programming — connects MQTT, databases, APIs and other services via drag&drop in the browser. | ~400 MB | 1880 |
| 3 | **n8n** | Workflow automation — similar to Node-RED but focused on business automation (emails, webhooks, API integrations, 400+ connectors). | ~1 GB | 5678 |
| 4 | **InfluxDB 1.x** | Time-series database 1.x (legacy InfluxQL) — stores time-series data from sensors (temperature, humidity, consumption). Template: `influxdb` in `.templates/`, image `influxdb:1.11`. Suitable for Node-RED and Grafana with the `influxdb_v1` plugin. | ~280 MB | 8086 |
| 4b | **InfluxDB 2.x** | Time-series database 2.x (Flux query language, built-in UI, organizations + buckets). Template: `influxdb2`. Suitable for new projects. | ~360 MB | 8086 |
| 4c | **Homebridge** | HomeKit bridge — exposes IoT devices (Mosquitto, Wi-Fi plugins, …) into the Apple Home app. Runs in `network_mode: host` (requires mDNS/Bonjour). UI port 8581. | ~600 MB | 8581 |
| 5 | **Grafana** | Dashboards and visualization — produces graphs and overviews from InfluxDB and other sources. Alerting, dashboard sharing. | ~1 GB | 3000 |
| 6 | **Portainer-CE** | Docker management UI — web interface for managing containers, images, networks, and volumes. Convenient alternative to the CLI. | ~300 MB | 9000/9443 |
| 7 | **Telegraf** | Metrics collection agent — gathers system metrics (CPU, RAM, disk, network) and sends them to InfluxDB. | ~300 MB | — |
| 8 | **Adminer** | Lightweight web DB administrator — alternative to phpMyAdmin for MariaDB/PostgreSQL/SQLite. | ~90 MB | 8080 |
| 9 | **WireGuard** | VPN tunnel — secure remote access to the IoT network from anywhere. Modern, fast, minimal overhead. | ~100 MB | 51820/udp |
| 10 | **Pi-hole** | DNS sinkhole — blocks ads and trackers at the DNS level for the whole network. | ~400 MB | 53, 80 |
| 11 | **Zigbee2MQTT** | Zigbee bridge — control Zigbee devices (bulbs, sensors, plugs) over MQTT without a proprietary hub. Requires a Zigbee USB adapter. | ~400 MB | 8081 |
| 12 | **Home Assistant** | Home automation — comprehensive smart-home platform with thousands of devices and automations supported. | ~1.5 GB | 8123 |
| 13 | **ESPHome** | Firmware for ESP8266/ESP32 — configure and flash IoT sensors via web UI, automatic Home Assistant integration. | ~500 MB | 6052 |
| 14 | **MariaDB** | Relational database — MySQL-compatible DB for structured data, users, configurations. | ~400 MB | 3306 |
| 15 | **PostgreSQL** | Advanced relational database — more robust alternative to MariaDB, used by n8n, Grafana, etc. | ~400 MB | 5432 |

The user picks numbers or service names. Confirm the selection and warn about:
- Total estimated size (sum of images)
- Whether everything fits on disk
- Recommended dependencies (e.g. Grafana typically needs InfluxDB, Zigbee2MQTT needs Mosquitto)

### Phase 3: Install Prerequisites

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git python3 python3-pip python3-dev jq
```

### Phase 4: Install Docker

If Docker is NOT installed:

```bash
# Add Docker GPG key and repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# For Debian:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# For Ubuntu/Raspberry Pi OS — adjust URL:
# https://download.docker.com/linux/ubuntu for Ubuntu
# https://download.docker.com/linux/raspbian for Raspberry Pi OS (32-bit)

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Add user to the docker group:**

```bash
# Prefer usermod:
sudo usermod -aG docker $USER

# If usermod is disabled, edit /etc/group directly:
# First check current members and append the new user:
CURRENT=$(grep "^docker:" /etc/group | cut -d: -f4)
if [ -z "$CURRENT" ]; then
  sudo sed -i "s/^docker:x:\([0-9]*\):$/docker:x:\1:$USER/" /etc/group
else
  sudo sed -i "s/^docker:x:\([0-9]*\):${CURRENT}$/docker:x:\1:${CURRENT},$USER/" /etc/group
fi
```

**Verify Docker:**
```bash
sg docker "docker --version && docker compose version"
```

### Phase 5: Clone IOTstack

```bash
git clone -b master https://github.com/SensorsIot/IOTstack.git ~/IOTstack
```

Create directories ONLY for the services the user selected:
```bash
# Example for mosquitto + nodered + portainer:
mkdir -p ~/IOTstack/volumes/mosquitto/{config,data,log,pwfile}
mkdir -p ~/IOTstack/volumes/nodered/{data,ssh}
mkdir -p ~/IOTstack/volumes/portainer-ce/data
mkdir -p ~/IOTstack/services/nodered
```

### Phase 6: Service Configuration

#### Mosquitto config
Create `~/IOTstack/volumes/mosquitto/config/mosquitto.conf`:
```
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
```

#### Node-RED Dockerfile
Create `~/IOTstack/services/nodered/Dockerfile`:
```dockerfile
ARG DOCKERHUB_TAG=latest
FROM nodered/node-red:${DOCKERHUB_TAG}
ARG EXTRA_PACKAGES
USER root
RUN apk add --no-cache eudev-dev ${EXTRA_PACKAGES}
USER node-red
```

#### docker-compose.yml
Use templates from `~/IOTstack/.templates/*/service.yml` as the base. Always set:
- `TZ=Europe/Prague` (or the user's timezone)
- `restart: unless-stopped` for all services
- Correct `depends_on` (nodered depends on mosquitto, grafana on influxdb)

**Reference ports:**
| Service | Port |
|--------|------|
| Mosquitto | 1883 |
| Node-RED | 1880 |
| n8n | 5678 |
| InfluxDB 1.x / 2.x | 8086 |
| Grafana | 3000 |
| Homebridge UI | 8581 (host net) |
| Portainer | 8000, 9000, 9443 |
| Telegraf | — (agent) |
| Adminer | 8080 |
| WireGuard | 51820/udp |
| Pi-hole | 53, 80 |
| Zigbee2MQTT | 8081 |
| Home Assistant | 8123 |
| ESPHome | 6052 |
| MariaDB | 3306 |
| PostgreSQL | 5432 |
| Tailscale | — (overlay, no open port) |

**IMPORTANT:** Use `docker compose` (v2), NOT `docker-compose` (v1), if the server has the Docker Compose plugin.

#### Manual compose build (alternative to menu.sh)

`~/IOTstack/menu.sh` is an interactive TUI (the `blessed` library) — **it cannot reasonably be driven over SSH non-interactively**. If you need automation (Claude/CI), build `docker-compose.yml` manually from the service.yml fragments under `~/IOTstack/.templates/<service>/service.yml`. Rules:

- **Mosquitto**: build context `./.templates/mosquitto/.` works out of the box (Dockerfile, docker-entrypoint.sh, iotstack_defaults are already in the template). No copying needed. Default config allows anonymous + listener 1883.
- **Node-RED**: requires rendering the Dockerfile into `services/nodered/`. The build script (`build.py`) is interactive (allows addon selection), but can be replaced manually:
  ```bash
  mkdir -p services/nodered
  sed 's|%run npm install modules list%||' .templates/nodered/Dockerfile.template > services/nodered/Dockerfile
  ```
  Additional addons (`node-red-contrib-*`) can be installed later via the Palette Manager in the UI.
- **InfluxDB 1.x vs 2.x**: `.templates/influxdb/` = `image: influxdb:1.11`, `.templates/influxdb2/` = 2.x. Pick one, not both (port 8086 conflict).
- **Homebridge**: `network_mode: host` — the `ports` section is ignored; UI port is controlled via `HOMEBRIDGE_CONFIG_UI_PORT=8581`.
- **Validate**: `docker compose config --quiet` before `up`.

### Phase 7: Install Aliases — GLOBALLY for all users

**Aliases install into `/etc/profile.d/` so they work for ALL system users, including future ones.**

```bash
# Clone aliases into a shared location
sudo git clone https://github.com/iotcz-cz/IOTstackAliases.git /opt/IOTstackAliases

# If the server uses Docker Compose v2 (plugin), patch the aliases:
# CAUTION: patch ONLY the docker-compose command, NOT the docker-compose.yml filename!
sudo sed -i "s/docker-compose -f/docker compose -f/g" /opt/IOTstackAliases/dot_iotstack_aliases

# Symlink into /etc/profile.d/ — loaded for every login shell, every user
sudo cp /opt/IOTstackAliases/dot_iotstack_aliases /etc/profile.d/iotstack_aliases.sh
sudo chmod 644 /etc/profile.d/iotstack_aliases.sh
```

**DO NOT use per-user installation in `~/.bashrc`** — it doesn't work for other users and requires manual setup for every new user.

### Phase 8: Start the Stack

```bash
cd ~/IOTstack
sg docker "docker compose up -d"
```

Verify:
```bash
sg docker "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
df -h /
```

### Phase 8.5: Tailscale VPN Tunnel (optional, recommended for remote access)

Tailscale provides an overlay VPN with no open ports — the server is reachable from any tailnet device under a stable `100.x.x.x` address or `<hostname>.<tailnet>.ts.net` name.

```bash
curl -fsSL https://tailscale.com/install.sh | sudo sh
sudo tailscale up --ssh --accept-routes
```

- `--ssh` — Tailscale SSH (ssh over the tailnet without exposing port 22 to the internet, ACL via the admin console)
- `--accept-routes` — server accepts subnet routes from other tailnet devices
- Optional: `--advertise-routes=192.168.x.0/24` (server as a LAN gateway), `--advertise-exit-node` (server as an exit node)

**Auth flow:** `tailscale up` prints a URL like `https://login.tailscale.com/a/<token>` — the user opens it in a browser, logs in, and approves the device. If you have an auth-key (from the admin console), use `--auth-key=tskey-...` and auth runs non-interactively.

**Verification:**
```bash
tailscale ip -4    # prints 100.x.x.x
tailscale status   # tailnet peers overview
```

**Note:** After `--accept-routes`, routes are accepted, but on Linux you may need `sudo tailscale up --accept-routes` again after a reboot for routes to apply (Tailscale usually does this automatically via the systemd unit).

### Phase 9: Final Report

At the end of installation, always show the user a clear summary:

1. **Running services** — name, port, URL (`http://IP:port`)
2. **Available aliases** with explanations:

| Alias | Function |
|-------|----------|
| `UP` | Start the whole stack |
| `DOWN` | Stop the whole stack |
| `BUILD` | Start the stack with image build |
| `REBUILD` | Rebuild images without cache |
| `PULL` | Pull new image versions |
| `RESTART` | Restart containers |
| `RECREATE` | Force-recreate containers |
| `TERMINATE` | Remove containers |
| `PRUNE` | Clean unused Docker objects |
| `DPS [container]` | Container status |
| `DNET [container]` | Container ports |
| `I` | `cd ~/IOTstack` |
| `S` | `cd ~/IOTstack/services` |
| `T` | `cd ~/IOTstack/.templates` |
| `V` | `cd ~/IOTstack/volumes` |
| `NODERED_DATA` | `cd` into Node-RED data |
| `<CONTAINER>_SHELL` | Shell into a container (uppercase name) |
| `aktualizuj` | `apt update && upgrade` |
| `REBOOT` / `SHUTDOWN` | Restart/shutdown with logging |

3. **Disk state** — how much space remains after install
4. **Next steps** — what needs configuring (passwords, Portainer initial setup, etc.)
5. **Notice** — aliases become active after a fresh login (or `source /etc/profile.d/iotstack_aliases.sh`)

## Key Principles

- **Always check disk** before pulling images — large images (Grafana ~1 GB, n8n ~1 GB, InfluxDB ~400 MB) can fill the disk
- **ALWAYS ask which services to install** — show the catalog with descriptions and sizes, let the user pick
- **If you run out of space** — clean up (`docker system prune -af`) and shrink the stack
- **Test after every step** — do not proceed if the previous step failed
- **Stay idempotent** — the skill must be safe to re-run without damaging an existing install
- **Aliases always globally** — install into `/etc/profile.d/`, never per-user in `.bashrc`. **EXCEPTION:** PiBuilder installs them per-user for `pi` (sources `~/.local/IOTstackAliases/dot_iotstack_aliases` from `~pi/.bashrc`) — leave that as is, but remember IOTstack work has to be done as `pi` (`sudo -u pi -i`).
- **Warn about security** — Mosquitto with `allow_anonymous true` is fine for LAN only, not the internet. Tailscale tunnel handles remote access without open ports.
- **Docker Compose version** — detect automatically, patch aliases if v2 (plugin)
- **Pi over Wi-Fi is the bottleneck** — first build (mosquitto + nodered + image pulls) takes ~10 min. Use `run_in_background` for `docker compose up -d`.

## Common pitfalls (from real deployments)

1. **`userconfig.service` blocks multi-user.target** (RPi imager wizard left hanging on tty8) → `argononed` waits in queue as `inactive (dead)`. Fix in Phase 0.
2. **`menu.sh` does not work over non-interactive SSH** — requires `blessed` TUI. Build the compose manually (Phase 6).
3. **`network_mode: host` on Homebridge** + other services with `ports:` on the same port = conflict. Homebridge needs host mode for HomeKit pairing mDNS — do not change.
4. **`.env` defaults to `TZ=Europe/London`** (after PiBuilder) — always check and adjust per the user.
5. **InfluxDB 1.x healthcheck** uses `curl http://localhost:8086` — `curl` must be in the image (it is in `influxdb:1.11`); some 2.x variants lack it.
6. **Mosquitto build context** is `./.templates/mosquitto/.` (with the trailing dot) — without the dot, compose breaks with "no such file" for the Dockerfile.
7. **Tailscale `--ssh` collision with sshd** — Tailscale SSH runs in parallel and does not interfere with sshd. It only targets tailnet connections.
