---
name: homebridge-camera-homekit
description: Přidání IP kamery (Dahua / TP-Link VIGI / Hikvision / ONVIF) do Apple Home přes Homebridge + homebridge-camera-ui na IOTstack serverech (oznu/homebridge image). Řeší RTSP discovery, config.json, unbridged pairing a hlavně upgrade Node.js + config-ui-x uvnitř starého oznu image. Použij když chce uživatel připojit kameru do Apple Home / HomeKit přes homebridge, replikovat setup mezi IOTstack servery, nebo debugovat camera-ui crash (tracingChannel / pty.node).
argument-hint: "[ssh-command] [camera-ip]"
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
effort: high
triggers:
  - homebridge
  - homebridge-camera-ui
  - Apple Home kamera
  - HomeKit kamera
  - IP kamera do Home
  - RTSP homebridge
  - tracingChannel
  - pty.node
  - VIGI
  - oznu/homebridge
---

# Homebridge → Apple Home: IP kamera

Expert na přidání IP kamery do Apple Home přes **Homebridge + homebridge-camera-ui** na IOTstack serverech (Debian / Raspberry Pi, image `oznu/homebridge:latest`). Postupuj systematicky, ověřuj každý krok.

## Vstupní parametry

- `$ARGUMENTS` — SSH příkaz k serveru (např. `ssh -i key/id_ed25519_claudeIA claudeIA@192.168.153.245`) + IP kamery.

Když chybí, zeptej se na SSH přístup a IP kamery. Přihlašovací údaje ke kameře (user/heslo) vždy vyžádej od uživatele — nejsou nikde v configu.

## Architektura (jak to funguje)

- Homebridge běží jako kontejner `oznu/homebridge:latest`, `network_mode: host`, volume `./volumes/homebridge:/homebridge`. Config UI na `:8581`.
- Plugin **homebridge-camera-ui** přidá platformu `CameraUI` s polem `cameras[]`; vlastní web UI na `:8081`.
- Kamery jsou **`unbridged: true`** → v Apple Home se každá přidává jako **samostatné zařízení** (HomeKit neumí video přes bridge). Setup code = **PIN bridge** z `config.json`.
- Video jde přes **ffmpeg** (`vcodec: copy` = žádný transcode, šetří CPU Pi).

## Postup

### Krok 1 — Zjisti, co je kamera zač (RTSP discovery)

```bash
SSH="ssh -i key/... user@server"; CAM="192.168.153.220"; C="admin:HESLO"
# web fingerprint (Dahua/TP-Link "IPC"/VIGI, Hikvision):
$SSH "curl -sk -m8 -i https://$CAM/ | head -20"
# RTSP živý?
$SSH "printf 'OPTIONS rtsp://$CAM:554/ RTSP/1.0\r\nCSeq: 1\r\n\r\n' | nc -w3 $CAM 554 | head"
# najdi funkční RTSP cestu + kodek/rozlišení (ffprobe na hostu, pokud je):
for p in "cam/realmonitor?channel=1&subtype=0" "cam/realmonitor?channel=1&subtype=1" \
         "stream1" "stream2" "Streaming/Channels/101" "Streaming/Channels/102"; do
  printf "%-40s -> " "$p"
  $SSH "timeout 10 ffprobe -v error -rtsp_transport tcp -i 'rtsp://$C@$CAM:554/$p' \
        -show_entries stream=codec_name,width,height -of csv=p=0 2>&1 | head -1"
done
```

Typické RTSP cesty podle výrobce:
| Výrobce | Main stream | Sub stream |
|---------|-------------|------------|
| **Dahua** | `cam/realmonitor?channel=1&subtype=0` | `...subtype=1` |
| **TP-Link VIGI** | `stream1` | `stream2` |
| **Hikvision** | `Streaming/Channels/101` | `Streaming/Channels/102` |
| **ONVIF generic** | zjisti z web UI / `onvif` | — |

**⚠️ HomeKit neumí H.265/HEVC.** Pokud je main stream H.265 (běžné u 4K), použij **H.264 sub stream** pro `source`/`subSource`/`stillImageSource` s `vcodec: copy`. Transcode H.265→H.264 na Pi 4 procesor nezvládne. Případně přepni main stream kamery na H.264 ve web UI, chceš-li vyšší rozlišení v Home.

### Krok 2 — Ověř přihlašovací údaje

401 = špatné heslo, 404 = špatná cesta (heslo OK). Digest auth:
```bash
$SSH "curl -sk -m6 --digest -u '$C' 'https://$CAM/cgi-bin/magicBox.cgi?action=getDeviceType'"
```

### Krok 3 — Instaluj plugin homebridge-camera-ui

Verzi drž shodnou napříč servery (referenční: **5.0.27**). Instaluje se do volume:
```bash
$SSH "docker exec -w /homebridge homebridge npm install homebridge-camera-ui@5.0.27 --save --no-audit --no-fund"
$SSH "sudo ls -d /home/pi/IOTstack/volumes/homebridge/node_modules/homebridge-camera-ui && echo OK"
```

### Krok 4 — ⚠️ KLÍČOVÉ: dorovnej Node.js + config-ui-x (jinak camera-ui crashne)

**Problém:** image `oznu/homebridge:latest` je deprecated a na Docker Hubu **zamrzlý na buildu z 2023-01-08 s Node 18**. `docker pull` nic nestáhne. camera-ui 5.x ale vyžaduje **Node ≥ 20** (jinak `TypeError: (0 , U.tracingChannel) is not a function` z `lru-cache` 11.x → homebridge spadne). Servery, kde kamera funguje (např. Tyršova), mají Node 22 upgradovaný **uvnitř běžícího kontejneru** — v RW vrstvě.

**Zkontroluj Node verzi:**
```bash
$SSH "docker exec homebridge node -v"   # potřebuješ >= 20; oznu 2023 image má v18.13.0
```

Pokud < 20, proveď **v tomto pořadí** (jinak se to nechytne):

```bash
# 4a. Node 18 -> 22 (node se přepne; rebuild starého config-ui-x node-pty ale SELŽE -> to je OK, řeší 4b)
$SSH "docker exec -u root homebridge hb-service update-node 22.18.0"

# 4b. config-ui-x -> 5.4.0 (starý 4.50.2 má node-pty-prebuilt-multiarch nekompat s node22
#     -> 'Cannot find module pty.node' shodí CELÝ homebridge; 5.x má moderní node-pty 0.13.1)
$SSH "docker exec -u root homebridge npm install -g --unsafe-perm --no-audit --no-fund homebridge-config-ui-x@5.4.0"

# 4c. restart (proběhne 1x jednorázový supervisor-restart = config migrace, pak stabilní)
$SSH "docker restart homebridge"
```

### Krok 5 — Zapiš config.json

Zálohuj původní: `sudo cp .../config.json .../config.json.bak-$(date +%Y%m%d-%H%M%S)`.
Zachovej `bridge` blok beze změny, přidej platformu `CameraUI` do `platforms[]`. Šablona jedné kamery viz `references/config-camera.json`. Klíčové:
- `unbridged: true`, `hsv: true`, `vcodec: "copy"`
- `videoProcessor: "/usr/local/bin/ffmpeg"` — **container ffmpeg 5.0** (má libfdk_aac + libx264). Cesta `.../ffmpeg-for-homebridge/ffmpeg` často NEexistuje (postinstall download selhává na Pi) → použij `/usr/local/bin/ffmpeg`.

Ověř JSON a restartuj:
```bash
$SSH "python3 -c 'import json;json.load(open(\"/home/pi/IOTstack/volumes/homebridge/config.json\"))' && echo valid && docker restart homebridge"
```

### Krok 6 — Ověření (než pošleš uživatele párovat)

```bash
$SSH "docker ps --filter name=homebridge --format '{{.Status}}'"        # stabilní uptime
$SSH "curl -s -m5 -o /dev/null -w 'ui:%{http_code}\n' http://SERVER:8581/"   # 200
$SSH "curl -s -m5 -o /dev/null -w 'cam:%{http_code}\n' http://SERVER:8081/"  # 200
# žádný restart-loop:
$SSH "sudo tail -80 .../homebridge.log | sed 's/\x1b\[[0-9;]*m//g' | grep -icE 'pty.node|SIGTERM|tracingChannel'"
# end-to-end: ffmpeg v kontejneru vytáhne 1 snímek
$SSH "docker exec homebridge sh -c \"timeout 20 /usr/local/bin/ffmpeg -hide_banner -rtsp_transport tcp -i 'rtsp://$C@$CAM:554/stream2' -frames:v 1 -f image2 -y /tmp/snap.jpg 2>&1 | tail -2; ls -la /tmp/snap.jpg\""
# najdi Setup Code:
$SSH "sudo tail -60 .../homebridge.log | sed 's/\x1b\[[0-9;]*m//g' | grep -iE 'running on port|Setup Code'"
```

### Krok 7 — Párování v Apple Home (uživatel)

Kamera je unbridged → **samostatné zařízení**:
1. iPhone na stejné LAN jako server.
2. Home app → **+** → Přidat příslušenství → **Více možností** → vyber accessory (`<Jmeno> XXXX`).
3. Zadej **Setup Code = PIN bridge** z `config.json` (formát `xxx-xx-xxx`).

## Gotchas (shrnutí)

- **`docker compose up -d homebridge` / recreate = REGRESE** — smaže Node 22 + config-ui 5.4.0 (jsou v container RW vrstvě, NE ve volume). Plugin ve volume přežije, ale camera-ui zas spadne na Node 18. Po nutném recreate zopakuj krok 4.
- **`tracingChannel is not a function`** → Node < 20, řeš krokem 4a.
- **`Cannot find module '../build/Release/pty.node'`** → starý config-ui-x na novém Node, řeš krokem 4b.
- **ffmpeg-for-homebridge chybí** → použij `/usr/local/bin/ffmpeg` (container ffmpeg 5.0).
- **H.265 main stream** → HomeKit ho neumí, ber H.264 sub stream.
- **401 vs 404** na RTSP: 401 = heslo, 404 = cesta.

## Reference

- `references/config-camera.json` — kompletní šablona `CameraUI` platformy + kamery.
- Ověřeno na IOTstack3 (Tyršova, 4 kamery) a IOTstack2 (Sibiř, TP-Link VIGI), oba `oznu/homebridge:latest` + Node 22 + config-ui-x 5.4.0 + camera-ui 5.0.27.
