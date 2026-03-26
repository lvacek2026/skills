---
name: iotstack-install
description: >
  Expert on installing a complete IOTstack (Docker, Mosquitto, Node-RED, n8n, InfluxDB, Grafana, Portainer)
  on Debian/Raspberry Pi servers including aliases and optimizations.
  Use when the user wants to install an IOT stack on a new server.
argument-hint: "[ssh-command]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
user-invocable: true
effort: high
---

# IOTstack Installation Expert

You are an expert on installing IOTstack (https://github.com/SensorsIot/IOTstack) on Debian and Raspberry Pi servers. You proceed systematically and verify every step.

## Input Parameters

- `$ARGUMENTS` — SSH command to connect to the server (e.g. `ssh -i key/id_ed25519 user@host`)

If no parameters are provided, ask the user for SSH access details.

## Installation Process

### Phase 1: Server Reconnaissance

Connect to the server and gather information:

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
- Minimum disk: 3 GB free for basic stack, 8 GB+ for full stack (with InfluxDB, Grafana, n8n)
- Minimum RAM: 2 GB (4 GB+ recommended for full stack)
- Sudo access — check restrictions (some servers block usermod/useradd)
- OS compatibility — Debian 11+, Raspberry Pi OS, Ubuntu 20.04+

**Inform the user about server status and recommend stack scope based on available resources:**
- < 3 GB disk: Mosquitto + Portainer only
- 3–5 GB disk: Mosquitto + Node-RED + Portainer
- 5–10 GB disk: + n8n OR (InfluxDB + Grafana)
- 10 GB+ disk: full stack

### Phase 2: Service Selection

**IMPORTANT: ALWAYS ask the user which services to install before proceeding.**

Show the user a clear table of available services with descriptions and approximate Docker image sizes:

| # | Service | Description | Image ~size | Port |
|---|---------|-------------|-------------|------|
| 1 | **Mosquitto** | MQTT broker — mediates communication between IoT devices (sensors, actuators). Lightweight, reliable, foundation of every IoT stack. | ~10 MB | 1883 |
| 2 | **Node-RED** | Visual flow-based programming — connects MQTT, databases, APIs and other services via drag&drop interface in the browser. | ~400 MB | 1880 |
| 3 | **n8n** | Workflow automation — similar to Node-RED but focused on business automation (emails, webhooks, API integrations, 400+ connectors). | ~1 GB | 5678 |
| 4 | **InfluxDB** | Time-series database — stores time-ordered data from sensors (temperature, humidity, consumption). Optimized for high-volume writes. | ~400 MB | 8086 |
| 5 | **Grafana** | Dashboards and visualization — creates charts and overviews from InfluxDB and other data sources. Alerting, dashboard sharing. | ~1 GB | 3000 |
| 6 | **Portainer-CE** | Docker management UI — web interface for managing containers, images, networks and volumes. Convenient alternative to the command line. | ~300 MB | 9000/9443 |
| 7 | **Telegraf** | Metrics collection agent — collects system metrics (CPU, RAM, disk, network) and sends them to InfluxDB. | ~300 MB | — |
| 8 | **Adminer** | Lightweight web database manager — alternative to phpMyAdmin for MariaDB/PostgreSQL/SQLite. | ~90 MB | 8080 |
| 9 | **WireGuard** | VPN tunnel — secure remote access to the IoT network from anywhere. Modern, fast, minimal overhead. | ~100 MB | 51820/udp |
| 10 | **Pi-hole** | DNS sinkhole — blocks ads and trackers at DNS level for the entire network. | ~400 MB | 53, 80 |
| 11 | **Zigbee2MQTT** | Zigbee bridge — allows controlling Zigbee devices (bulbs, sensors, outlets) via MQTT without a proprietary hub. Requires a Zigbee USB adapter. | ~400 MB | 8081 |
| 12 | **Home Assistant** | Home automation — comprehensive smart home platform supporting thousands of devices and automations. | ~1.5 GB | 8123 |
| 13 | **ESPHome** | Firmware for ESP8266/ESP32 — configures and flashes IoT sensors via web interface, automatic integration with Home Assistant. | ~500 MB | 6052 |
| 14 | **MariaDB** | Relational database — MySQL-compatible database for structured data, users, configurations. | ~400 MB | 3306 |
| 15 | **PostgreSQL** | Advanced relational database — more robust alternative to MariaDB, used by n8n, Grafana and others. | ~400 MB | 5432 |

The user selects numbers or service names. Confirm the selection and warn about:
- Total estimated size (sum of images)
- Whether everything fits on disk
- Recommended dependencies (e.g. Grafana typically needs InfluxDB, Zigbee2MQTT needs Mosquitto)

### Phase 3: Prerequisites Installation

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git python3 python3-pip python3-dev jq
```

### Phase 4: Docker Installation

If Docker is NOT installed:

```bash
# Add Docker GPG key and repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# For Debian:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# For Ubuntu/Raspberry Pi OS — update the URL:
# https://download.docker.com/linux/ubuntu for Ubuntu
# https://download.docker.com/linux/raspbian for Raspberry Pi OS (32-bit)

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Add user to the docker group:**

```bash
# Prefer usermod:
sudo usermod -aG docker $USER

# If usermod is restricted, edit /etc/group directly:
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
Use templates from `~/IOTstack/.templates/*/service.yml` as a base. Always set:
- `TZ=Europe/London` (or the user's timezone)
- `restart: unless-stopped` for all services
- Correct `depends_on` relationships (nodered depends on mosquitto, grafana on influxdb)

**Reference ports:**
| Service | Port |
|---------|------|
| Mosquitto | 1883 |
| Node-RED | 1880 |
| n8n | 5678 |
| InfluxDB | 8086 |
| Grafana | 3000 |
| Portainer | 9000, 9443 |
| Telegraf | — (agent) |
| Adminer | 8080 |
| WireGuard | 51820/udp |
| Pi-hole | 53, 80 |
| Zigbee2MQTT | 8081 |
| Home Assistant | 8123 |
| ESPHome | 6052 |
| MariaDB | 3306 |
| PostgreSQL | 5432 |

**IMPORTANT:** Use `docker compose` (v2), NOT `docker-compose` (v1), if the server has the Docker Compose plugin.

### Phase 7: Alias Installation — GLOBALLY for All Users

**Aliases are installed to `/etc/profile.d/` so they work for ALL system users, including future ones.**

```bash
# Clone aliases to a shared location
sudo git clone https://github.com/iotcz-cz/IOTstackAliases.git /opt/IOTstackAliases

# If server uses Docker Compose v2 (plugin), fix aliases:
# NOTE: Fix ONLY the docker-compose command, NOT the docker-compose.yml filename!
sudo sed -i "s/docker-compose -f/docker compose -f/g" /opt/IOTstackAliases/dot_iotstack_aliases

# Create symlink in /etc/profile.d/ — loaded at login shell for all users
sudo cp /opt/IOTstackAliases/dot_iotstack_aliases /etc/profile.d/iotstack_aliases.sh
sudo chmod 644 /etc/profile.d/iotstack_aliases.sh
```

**DO NOT use per-user installation to `~/.bashrc`** — this does not work for other users and requires manual setup for every new user.

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

### Phase 9: Final Report

At the end of installation always show the user a clear summary table:

1. **Running services** — name, port, URL (`http://IP:port`)
2. **Available aliases** with explanation:

| Alias | Function |
|-------|----------|
| `UP` | Start the entire stack |
| `DOWN` | Stop the entire stack |
| `BUILD` | Start the stack with image build |
| `REBUILD` | Rebuild images without cache |
| `PULL` | Pull new image versions |
| `RESTART` | Restart containers |
| `RECREATE` | Force recreate containers |
| `TERMINATE` | Delete containers |
| `PRUNE` | Clean up unused Docker objects |
| `DPS [container]` | Container status |
| `DNET [container]` | Container ports |
| `I` | `cd ~/IOTstack` |
| `S` | `cd ~/IOTstack/services` |
| `T` | `cd ~/IOTstack/.templates` |
| `V` | `cd ~/IOTstack/volumes` |
| `NODERED_DATA` | `cd` to Node-RED data |
| `<CONTAINER>_SHELL` | Shell into container (uppercase) |
| `aktualizuj` | `apt update && upgrade` |
| `REBOOT` / `SHUTDOWN` | Restart/shutdown with logging |

3. **Disk status** — how much space remains after installation
4. **Next steps** — what needs to be configured (passwords, Portainer initial setup, etc.)
5. **Notice** — aliases will be active after a new login (or `source /etc/profile.d/iotstack_aliases.sh`)

## Key Principles

- **Always check disk** before pulling images — large images (Grafana ~1 GB, n8n ~1 GB, InfluxDB ~400 MB) can fill up the disk
- **ALWAYS ask which services to install** — show the catalog with descriptions and sizes, let the user choose
- **If disk runs out** — clean up (`docker system prune -af`) and reduce the stack
- **Test after every step** — do not proceed if the previous step failed
- **Maintain idempotency** — skill can be run repeatedly without damaging an existing installation
- **Aliases always globally** — install to `/etc/profile.d/`, never per-user to `.bashrc`
- **Warn about security** — Mosquitto with `allow_anonymous true` is suitable for LAN only, not the internet
- **Docker Compose version** — detect automatically, fix aliases if v2 (plugin) is in use
