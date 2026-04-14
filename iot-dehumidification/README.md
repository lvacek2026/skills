# IoT Dehumidification Skill

Claude Code skill pro expertní řízení vysoušení s vazbou na fotovoltaickou výrobu.

## Instalace

```
/install-skill lvacek2026/iot-dehumidification-skill
```

## Co skill umí

- Řídí odvlhčování podle fyzikálních časových konstant (fáze stabilizace, separace, plná účinnost)
- Chrání kompresory před short-cyclingem a re-evaporací
- Pracuje s predikcí solární výroby (Solcast, Look-Ahead logika)
- Prioritizuje zařízení podle energetické efektivity (odvlhčovač vs. AC v Dry režimu)
- Udržuje persistenci stavu i přes restarty řídicího systému
