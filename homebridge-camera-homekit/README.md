# homebridge-camera-homekit

Skill pro přidání IP kamery (Dahua / TP-Link VIGI / Hikvision / ONVIF) do **Apple Home** přes **Homebridge + homebridge-camera-ui** na IOTstack serverech (`oznu/homebridge:latest`, Debian / Raspberry Pi).

## Co řeší

- RTSP discovery (fingerprint výrobce + hledání funkční stream cesty)
- Instalaci pluginu `homebridge-camera-ui`
- **Hlavní gotcha:** upgrade Node.js (18 → 22) + config-ui-x (4.x → 5.4.0) uvnitř starého zamrzlého oznu image — bez toho camera-ui 5.x crashuje (`tracingChannel` / `pty.node`)
- Zápis `config.json` (unbridged kamera, H.264 sub stream, `vcodec: copy`, container ffmpeg)
- Ověření (porty, restart-loop, end-to-end snímek) + pairing v Apple Home

## Použití

```
/homebridge-camera-homekit "ssh -i key/id_ed25519_claudeIA claudeIA@192.168.153.245" 192.168.153.220
```

Ověřeno na IOTstack3 (Tyršova, 4 kamery) a IOTstack2 (Sibiř, TP-Link VIGI) — 2026-08.

Viz `SKILL.md` pro plný postup, `references/config-camera.json` pro šablonu configu.
