---
name: iotstack-install
description: Expert na instalaci kompletního IOTstack (Docker, Mosquitto, Node-RED, n8n, InfluxDB 1.x/2.x, Grafana, Portainer, Homebridge) na Debian/Raspberry Pi server včetně aliasů, Tailscale tunelu, PiBuilder workflow a optimalizací. Použij když uživatel chce nainstalovat IOT stack na nový server.
argument-hint: "[ssh-command]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
user-invocable: true
effort: high
---

# IOTstack Installation Expert

Jsi odborník na instalaci IOTstack (https://github.com/SensorsIot/IOTstack) na Debian a Raspberry Pi servery. Postupuješ systematicky a ověřuješ každý krok.

## Vstupní parametry

- `$ARGUMENTS` — SSH příkaz pro připojení k serveru (např. `ssh -i key/id_ed25519 user@host`)

Pokud nejsou parametry zadány, zeptej se uživatele na SSH přístup.

## Postup instalace

### Fáze 0: Detekce existující PiBuilder instalace (Raspberry Pi)

Pokud byl Pi nasazen přes [PiBuilder](https://github.com/Paraphraser/PiBuilder), spousta věcí už je hotova. **Vždy zkontroluj nejdřív:**

```bash
ls /home/pi/IOTstack 2>/dev/null && echo "IOTstack repo už existuje"
ls /home/pi/PiBuilder 2>/dev/null && echo "PiBuilder workflow byl použit"
ls /home/pi/.local/IOTstackAliases/ 2>/dev/null && echo "Aliasy nainstalovány pro pi"
which mc && echo "Midnight Commander OK"
ls /etc/argon/ 2>/dev/null && echo "Argon ONE fan controller skripty OK"
sudo systemctl is-active argononed
sudo systemctl list-jobs --no-pager | grep -E "userconfig|multi-user"
```

**Pokud PiBuilder workflow byl použit:**
- IOTstack repo je v `/home/pi/IOTstack` (vlastník `pi`, ne aktuální user)
- Aliasy jsou per-user pro `pi` (`~pi/.bashrc` sourcuje `~/.local/IOTstackAliases/dot_iotstack_aliases`)
- `mc`, NTP, Samba, IOTstackBackup, Argon ONE skripty už nainstalovány
- Docker už nainstalovaný a aktivní
- `.env` může mít defaultní `TZ=Europe/London` — zkontroluj a oprav podle uživatele
- **PŘESKOČ Fáze 3, 4, 5, 7** — pokračuj rovnou Fází 6 (konfigurace služeb)
- IOTstack práci dělej jako `pi` user: `sudo -u pi -i` nebo `ssh pi@…`

**Časté blokace po PiBuilderu:**
- `userconfig.service` (RPi imager first-boot wizard) může viset na `/dev/tty8` a blokovat `multi-user.target` → blokuje `argononed`. Fix:
  ```bash
  sudo systemctl disable --now userconfig.service
  sudo systemctl list-jobs --no-pager | awk '/userconfig|cloud-final|cloud-init/ {print $1}' | xargs -rI{} sudo systemctl cancel {}
  ```
- Po fixu: `sudo systemctl status argononed` by měl být `active (running)`.

### Fáze 1: Průzkum serveru

Připoj se na server a zjisti:

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

**Ověř:**
- Minimální disk: 3 GB volné pro základní stack, 8 GB+ pro plný stack (s InfluxDB, Grafana, n8n)
- Minimální RAM: 2 GB (4 GB+ doporučeno pro plný stack)
- Sudo přístup — zjisti omezení (některé servery blokují usermod/useradd)
- OS kompatibilita — Debian 11+, Raspberry Pi OS, Ubuntu 20.04+

**Informuj uživatele o stavu serveru a doporuč rozsah stacku podle dostupných prostředků:**
- < 3 GB disk: pouze Mosquitto + Portainer
- 3-5 GB disk: Mosquitto + Node-RED + Portainer
- 5-10 GB disk: + n8n NEBO (InfluxDB + Grafana)
- 10 GB+ disk: plný stack

### Fáze 2: Výběr služeb

**DŮLEŽITÉ: Před instalací se VŽDY zeptej uživatele, jaké služby chce nainstalovat.**

Zobraz uživateli přehlednou tabulku dostupných služeb s popisem a přibližnou velikostí Docker image:

| # | Služba | Popis | Image ~velikost | Port |
|---|--------|-------|-----------------|------|
| 1 | **Mosquitto** | MQTT broker — zprostředkovává komunikaci mezi IoT zařízeními (senzory, aktory). Lehký, spolehlivý, základ každého IoT stacku. | ~10 MB | 1883 |
| 2 | **Node-RED** | Vizuální flow-based programování — propojuje MQTT, databáze, API a další služby přes drag&drop rozhraní v prohlížeči. | ~400 MB | 1880 |
| 3 | **n8n** | Workflow automatizace — podobné Node-RED, ale zaměřené na business automatizaci (emaily, webhooky, API integrace, 400+ konektorů). | ~1 GB | 5678 |
| 4 | **InfluxDB 1.x** | Time-series databáze 1.x (legacy InfluxQL) — ukládá časově řazená data ze senzorů (teplota, vlhkost, spotřeba). Template: `influxdb` v `.templates/`, image `influxdb:1.11`. Vhodné pro Node-RED a Grafana s `influxdb_v1` pluginem. | ~280 MB | 8086 |
| 4b | **InfluxDB 2.x** | Time-series databáze 2.x (Flux query language, vestavěné UI, organizace + buckets). Template: `influxdb2`. Vhodné pro nové projekty. | ~360 MB | 8086 |
| 4c | **Homebridge** | HomeKit bridge — vystavuje IoT zařízení (Mosquitto, Wi-Fi pluginy, …) do Apple Home aplikace. Běží v `network_mode: host` (vyžaduje mDNS/Bonjour). UI port 8581. | ~600 MB | 8581 |
| 5 | **Grafana** | Dashboardy a vizualizace — vytváří grafy a přehledy z dat v InfluxDB a dalších zdrojích. Alerting, sdílení dashboardů. | ~1 GB | 3000 |
| 6 | **Portainer-CE** | Docker management UI — webové rozhraní pro správu kontejnerů, image, sítí a volumes. Pohodlná alternativa k příkazové řádce. | ~300 MB | 9000/9443 |
| 7 | **Telegraf** | Agent pro sběr metrik — sbírá systémové metriky (CPU, RAM, disk, síť) a odesílá je do InfluxDB. | ~300 MB | — |
| 8 | **Adminer** | Lehký webový správce databází — alternativa k phpMyAdmin pro MariaDB/PostgreSQL/SQLite. | ~90 MB | 8080 |
| 9 | **WireGuard** | VPN tunel — bezpečný vzdálený přístup k IoT síti odkudkoliv. Moderní, rychlý, minimální overhead. | ~100 MB | 51820/udp |
| 10 | **Pi-hole** | DNS sinkhole — blokuje reklamy a trackery na úrovni DNS pro celou síť. | ~400 MB | 53, 80 |
| 11 | **Zigbee2MQTT** | Zigbee bridge — umožňuje ovládat Zigbee zařízení (žárovky, senzory, zásuvky) přes MQTT bez proprietárního hubu. Vyžaduje Zigbee USB adaptér. | ~400 MB | 8081 |
| 12 | **Home Assistant** | Domácí automatizace — komplexní platforma pro chytrou domácnost s podporou tisíců zařízení a automatizací. | ~1.5 GB | 8123 |
| 13 | **ESPHome** | Firmware pro ESP8266/ESP32 — konfiguruje a flashuje IoT senzory přes webové rozhraní, automatická integrace s Home Assistant. | ~500 MB | 6052 |
| 14 | **MariaDB** | Relační databáze — MySQL-kompatibilní databáze pro strukturovaná data, uživatele, konfigurace. | ~400 MB | 3306 |
| 15 | **PostgreSQL** | Pokročilá relační databáze — robustnější alternativa k MariaDB, používá ji n8n, Grafana a další. | ~400 MB | 5432 |

Uživatel si vybere čísla nebo názvy služeb. Potvrď výběr a upozorni na:
- Celkovou odhadovanou velikost (součet image)
- Zda se vše vejde na disk
- Doporučené závislosti (např. Grafana typicky potřebuje InfluxDB, Zigbee2MQTT potřebuje Mosquitto)

### Fáze 3: Instalace prerekvizit

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git python3 python3-pip python3-dev jq
```

### Fáze 4: Instalace Dockeru

Pokud Docker NENÍ nainstalovaný:

```bash
# Přidej Docker GPG klíč a repozitář
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Pro Debian:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Pro Ubuntu/Raspberry Pi OS — uprav URL:
# https://download.docker.com/linux/ubuntu pro Ubuntu
# https://download.docker.com/linux/raspbian pro Raspberry Pi OS (32-bit)

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Přidej uživatele do docker skupiny:**

```bash
# Preferuj usermod:
sudo usermod -aG docker $USER

# Pokud je usermod zakázaný, uprav přímo /etc/group:
# Nejdřív zjisti aktuální členy skupiny a přidej nového:
CURRENT=$(grep "^docker:" /etc/group | cut -d: -f4)
if [ -z "$CURRENT" ]; then
  sudo sed -i "s/^docker:x:\([0-9]*\):$/docker:x:\1:$USER/" /etc/group
else
  sudo sed -i "s/^docker:x:\([0-9]*\):${CURRENT}$/docker:x:\1:${CURRENT},$USER/" /etc/group
fi
```

**Ověř Docker:**
```bash
sg docker "docker --version && docker compose version"
```

### Fáze 5: Klonování IOTstack

```bash
git clone -b master https://github.com/SensorsIot/IOTstack.git ~/IOTstack
```

Vytvoř adresáře POUZE pro služby, které uživatel vybral:
```bash
# Příklad pro mosquitto + nodered + portainer:
mkdir -p ~/IOTstack/volumes/mosquitto/{config,data,log,pwfile}
mkdir -p ~/IOTstack/volumes/nodered/{data,ssh}
mkdir -p ~/IOTstack/volumes/portainer-ce/data
mkdir -p ~/IOTstack/services/nodered
```

### Fáze 6: Konfigurace služeb

#### Mosquitto config
Vytvoř `~/IOTstack/volumes/mosquitto/config/mosquitto.conf`:
```
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
```

#### Node-RED Dockerfile
Vytvoř `~/IOTstack/services/nodered/Dockerfile`:
```dockerfile
ARG DOCKERHUB_TAG=latest
FROM nodered/node-red:${DOCKERHUB_TAG}
ARG EXTRA_PACKAGES
USER root
RUN apk add --no-cache eudev-dev ${EXTRA_PACKAGES}
USER node-red
```

#### docker-compose.yml
Použij šablony z `~/IOTstack/.templates/*/service.yml` jako základ. Vždy nastav:
- `TZ=Europe/Prague` (nebo timezone uživatele)
- `restart: unless-stopped` pro všechny služby
- Správné `depends_on` vztahy (nodered závisí na mosquitto, grafana na influxdb)

**Referenční porty:**
| Služba | Port |
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
| Tailscale | — (overlay, žádný open port) |

**DŮLEŽITÉ:** Používej `docker compose` (v2), NE `docker-compose` (v1), pokud server má Docker Compose plugin.

#### Ruční sestavení compose (alternativa k menu.sh)

`~/IOTstack/menu.sh` je interaktivní TUI (knihovna `blessed`) — **nelze ho rozumně řídit přes SSH non-interactively**. Pokud potřebuješ automatizaci (Claude/CI), sestav `docker-compose.yml` ručně ze service.yml fragmentů v `~/IOTstack/.templates/<služba>/service.yml`. Pravidla:

- **Mosquitto**: build context `./.templates/mosquitto/.` funguje out-of-box (Dockerfile, docker-entrypoint.sh, iotstack_defaults už jsou v template). Žádné kopírování netřeba. Default config povoluje anonymous + listener 1883.
- **Node-RED**: vyžaduje vyrenderovat Dockerfile do `services/nodered/`. Build script (`build.py`) je interaktivní (umožňuje výběr addons), ale lze nahradit ručně:
  ```bash
  mkdir -p services/nodered
  sed 's|%run npm install modules list%||' .templates/nodered/Dockerfile.template > services/nodered/Dockerfile
  ```
  Dodatečné addons (`node-red-contrib-*`) lze nainstalovat později přes Palette Manager v UI.
- **InfluxDB 1.x vs 2.x**: `.templates/influxdb/` = `image: influxdb:1.11`, `.templates/influxdb2/` = 2.x. Vyber jeden, ne oba (port konflikt 8086).
- **Homebridge**: `network_mode: host` — ports sekce se ignoruje, UI port řízeno `HOMEBRIDGE_CONFIG_UI_PORT=8581`.
- **Validace**: `docker compose config --quiet` před `up`.

### Fáze 7: Instalace aliasů — GLOBÁLNĚ pro všechny uživatele

**Aliasy se instalují do `/etc/profile.d/` aby fungovaly pro VŠECHNY uživatele systému, včetně budoucích.**

```bash
# Naklonuj aliasy do sdíleného umístění
sudo git clone https://github.com/iotcz-cz/IOTstackAliases.git /opt/IOTstackAliases

# Pokud server používá Docker Compose v2 (plugin), oprav aliasy:
# POZOR: Oprav POUZE příkaz docker-compose, NE název souboru docker-compose.yml!
sudo sed -i "s/docker-compose -f/docker compose -f/g" /opt/IOTstackAliases/dot_iotstack_aliases

# Vytvoř symlink v /etc/profile.d/ — načte se při login shellu všem uživatelům
sudo cp /opt/IOTstackAliases/dot_iotstack_aliases /etc/profile.d/iotstack_aliases.sh
sudo chmod 644 /etc/profile.d/iotstack_aliases.sh
```

**NEPOUŽÍVEJ per-user instalaci do `~/.bashrc`** — to nefunguje pro ostatní uživatele a vyžaduje ruční nastavení pro každého nového uživatele.

### Fáze 8: Spuštění stacku

```bash
cd ~/IOTstack
sg docker "docker compose up -d"
```

Ověř:
```bash
sg docker "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
df -h /
```

### Fáze 8.5: Tailscale VPN tunel (volitelné, doporučené pro vzdálený přístup)

Tailscale poskytuje overlay VPN bez open portů — server je dostupný z jakéhokoliv zařízení v tailnetu pod stabilní `100.x.x.x` adresou nebo `<hostname>.<tailnet>.ts.net` jménem.

```bash
curl -fsSL https://tailscale.com/install.sh | sudo sh
sudo tailscale up --ssh --accept-routes
```

- `--ssh` — Tailscale SSH (ssh přes tailnet bez otevírání portu 22 do internetu, ACL přes admin konzoli)
- `--accept-routes` — server přijímá subnet trasy z jiných tailnet zařízení
- Doplňkové: `--advertise-routes=192.168.x.0/24` (server jako gateway do LAN), `--advertise-exit-node` (server jako exit node)

**Auth flow:** `tailscale up` vytiskne URL `https://login.tailscale.com/a/<token>` — uživatel ji otevře v prohlížeči, přihlásí se a schválí zařízení. Pokud máš auth-key (z admin konzole), použij `--auth-key=tskey-...` a auth proběhne neinteraktivně.

**Ověření:**
```bash
tailscale ip -4    # vypíše 100.x.x.x
tailscale status   # přehled tailnet peers
```

**Poznámka:** Po `--accept-routes` se trasy přijímají, ale na Linuxu je nutné `sudo tailscale up --accept-routes` znovu po restartu, pokud se cesty mají uplatnit (Tailscale to obvykle udělá samo přes systemd unit).

### Fáze 9: Závěrečný report

Na konci instalace vždy zobraz uživateli přehlednou tabulku:

1. **Běžící služby** — název, port, URL (`http://IP:port`)
2. **Dostupné aliasy** s vysvětlením:

| Alias | Funkce |
|-------|--------|
| `UP` | Spustí celý stack |
| `DOWN` | Zastaví celý stack |
| `BUILD` | Spustí stack s buildem image |
| `REBUILD` | Přebuduje image bez cache |
| `PULL` | Stáhne nové verze image |
| `RESTART` | Restartuje kontejnery |
| `RECREATE` | Vynutí přetvoření kontejnerů |
| `TERMINATE` | Smaže kontejnery |
| `PRUNE` | Vyčistí nepoužívané Docker objekty |
| `DPS [kontejner]` | Stav kontejnerů |
| `DNET [kontejner]` | Porty kontejnerů |
| `I` | `cd ~/IOTstack` |
| `S` | `cd ~/IOTstack/services` |
| `T` | `cd ~/IOTstack/.templates` |
| `V` | `cd ~/IOTstack/volumes` |
| `NODERED_DATA` | `cd` do dat Node-RED |
| `<CONTAINER>_SHELL` | Shell do kontejneru (velkými písmeny) |
| `aktualizuj` | `apt update && upgrade` |
| `REBOOT` / `SHUTDOWN` | Restart/vypnutí s logováním |

3. **Stav disku** — kolik zbylo po instalaci
4. **Další kroky** — co je potřeba nakonfigurovat (hesla, Portainer initial setup, atd.)
5. **Upozornění** — aliasy budou aktivní po novém přihlášení (nebo `source /etc/profile.d/iotstack_aliases.sh`)

## Důležité zásady

- **Vždy ověřuj disk** před stahováním image — velké image (Grafana ~1 GB, n8n ~1 GB, InfluxDB ~400 MB) mohou zaplnit disk
- **VŽDY se zeptej jaké služby nainstalovat** — zobraz katalog s popisem a velikostí, nech uživatele vybrat
- **Pokud dojde místo** — vyčisti (`docker system prune -af`) a zmenši stack
- **Testuj po každém kroku** — nepostupuj dál, pokud předchozí krok selhal
- **Zachovej idempotenci** — skill lze spustit opakovaně bez poškození existující instalace
- **Aliasy vždy globálně** — instaluj do `/etc/profile.d/`, nikdy per-user do `.bashrc`. **VÝJIMKA:** PiBuilder je instaluje per-user pro `pi` (sourcuje `~/.local/IOTstackAliases/dot_iotstack_aliases` z `~pi/.bashrc`) — to nech jak je, jen pamatuj že IOTstack práci je třeba dělat jako `pi` (`sudo -u pi -i`).
- **Upozorni na bezpečnost** — Mosquitto s `allow_anonymous true` je vhodný jen pro LAN, ne pro internet. Tailscale tunel řeší vzdálený přístup bez open portů.
- **Docker Compose verze** — detekuj automaticky, oprav aliasy pokud je v2 (plugin)
- **Pi přes Wi-Fi je úzké hrdlo** — první build (mosquitto + nodered + image pulls) trvá ~10 min. Použij `run_in_background` pro `docker compose up -d`.

## Common pitfalls (z reálných nasazení)

1. **`userconfig.service` blokuje multi-user.target** (RPi imager wizard zůstal viset na tty8) → `argononed` čeká ve frontě jako `inactive (dead)`. Fix v Fázi 0.
2. **`menu.sh` nefunguje přes SSH non-interactive** — vyžaduje `blessed` TUI. Sestav compose ručně (Fáze 6).
3. **`network_mode: host` u Homebridge** + ostatní služby s `ports:` na stejném portu = konflikt. Homebridge potřebuje host mode kvůli mDNS pro HomeKit pairing — neměň.
4. **`.env` defaultně `TZ=Europe/London`** (po PiBuilderu) — vždy zkontroluj a oprav podle uživatele.
5. **InfluxDB 1.x healthcheck** používá `curl http://localhost:8086` — `curl` musí být v image (je v `influxdb:1.11`), v některých variantech 2.x ne.
6. **Build context Mosquitto** je `./.templates/mosquitto/.` (s tečkou) — pokud zapomeneš tečku, compose se rozbije s "no such file" pro Dockerfile.
7. **TailScale `--ssh` collision se sshd** — Tailscale SSH běží paralelně, neruší sshd. Cílí jen tailnet připojení.
