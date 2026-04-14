# Homey API & Node-RED Integration Skill

Claude Code skill pro ovládání klimatizačních jednotek přes Homey platformu a Node-RED.

## Instalace

```
/install-skill lvacek2026/homey-node-red-skill
```

## Co skill umí

- Pomáhá s integrací Homey zařízení (zejména AC) přes Node-RED
- Generuje Node-RED flow JSON s uzly `homey-device-write`, `homey-device-read`, `homey-device-listen`
- Dodržuje správné datové typy Homey capabilities (`onoff`, `target_temperature`, `measure_temperature`)
- Navrhuje REST API volání i nativní Homey Apps SDK řešení
- Validuje payloady před odesláním do Homey API
