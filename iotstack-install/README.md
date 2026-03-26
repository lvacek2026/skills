# iotstack-install

Automated IOTstack installation expert for Debian and Raspberry Pi servers. Connects via SSH, checks server resources, lets you pick services, and installs the full stack with Docker, aliases and configuration.

## Install

```bash
npx skills add https://github.com/lvacek2026/skills --skill iotstack-install -g
```

## Usage

```
/iotstack-install ssh -i key/id_ed25519 user@192.168.1.10
```

Or invoke without arguments — the skill will ask for SSH access details.

## What It Does

1. **Server reconnaissance** — checks OS, architecture, CPU, RAM, disk, sudo access and Docker status
2. **Resource-based recommendation** — suggests stack scope based on available disk space
3. **Service selection** — shows full catalog of 15 services with descriptions and image sizes, lets you choose
4. **Prerequisites** — installs curl, git, python3, jq
5. **Docker installation** — adds official Docker repository, installs Docker CE + Compose plugin
6. **IOTstack clone** — clones from `SensorsIot/IOTstack`, creates only required directories
7. **Service configuration** — Mosquitto config, Node-RED Dockerfile, docker-compose.yml with correct dependencies
8. **Global aliases** — installs IOTstackAliases to `/etc/profile.d/` for all system users
9. **Stack launch** — starts all containers, verifies status
10. **Final report** — running services with URLs, alias reference, disk status, next steps

## Supported Services

| Service | Port | Description |
|---------|------|-------------|
| Mosquitto | 1883 | MQTT broker |
| Node-RED | 1880 | Visual flow programming |
| n8n | 5678 | Workflow automation |
| InfluxDB | 8086 | Time-series database |
| Grafana | 3000 | Dashboards & visualization |
| Portainer-CE | 9000/9443 | Docker management UI |
| Telegraf | — | Metrics collection agent |
| Adminer | 8080 | Web database manager |
| WireGuard | 51820/udp | VPN tunnel |
| Pi-hole | 53/80 | DNS ad blocker |
| Zigbee2MQTT | 8081 | Zigbee bridge (requires USB adapter) |
| Home Assistant | 8123 | Home automation platform |
| ESPHome | 6052 | ESP8266/ESP32 firmware manager |
| MariaDB | 3306 | Relational database |
| PostgreSQL | 5432 | Advanced relational database |

## Requirements

- Debian 11+, Raspberry Pi OS or Ubuntu 20.04+
- Minimum 3 GB free disk (8 GB+ recommended for full stack)
- Minimum 2 GB RAM (4 GB+ recommended)
- SSH access with sudo privileges
