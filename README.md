# Skills for Claude Code

A collection of custom skills for [Claude Code](https://claude.ai/code).

## Usage

```bash
npx skills add https://github.com/lvacek2026/skills --skill <name> -g
```

The `-g` flag installs the skill globally (available across all projects).

## Available Skills

| Skill | Description | Install |
|-------|-------------|---------|
| [liquid-glass](./liquid-glass/) | Apple Liquid Glass UI/UX design & SwiftUI implementation | `npx skills add https://github.com/lvacek2026/skills --skill liquid-glass -g` |
| [huawei-vrp](./huawei-vrp/) | Huawei CloudEngine S57xx/S67xx (VRP) – VLAN, Trunk, LACP, STP, SSH | `npx skills add https://github.com/lvacek2026/skills --skill huawei-vrp -g` |
| [iotstack-install](./iotstack-install/) | Automated IOTstack installer via SSH – Docker, Mosquitto, Node-RED, n8n, InfluxDB, Grafana | `npx skills add https://github.com/lvacek2026/skills --skill iotstack-install -g` |
| [homey-node-red](./homey-node-red/) | Homey API & Node-RED integrace – ovládání klimatizace a IoT zařízení | `npx skills add https://github.com/lvacek2026/skills --skill homey-node-red -g` |
| [iot-dehumidification](./iot-dehumidification/) | Expertní řízení vysoušení přes IoT s vazbou na FVE predikci | `npx skills add https://github.com/lvacek2026/skills --skill iot-dehumidification -g` |
| [n8n-slack-expert](./n8n-slack-expert/) | Stabilní integrace n8n + Slack – timeouty, idempotence, routing | `npx skills add https://github.com/lvacek2026/skills --skill n8n-slack-expert -g` |
| [grafana-energy-viz](./grafana-energy-viz/) | Návrh energetických dashboardů v Grafaně – Canvas Panel, Sankey, Solar Flow, animace toků (Tesla/Victron styl bez Enterprise) | `npx skills add https://github.com/lvacek2026/skills --skill grafana-energy-viz -g` |

## Repository Structure

```
skills/
├── liquid-glass/
│   ├── SKILL.md
│   └── README.md
├── huawei-vrp/
│   ├── SKILL.md
│   ├── README.md
│   └── references/
│       └── quickstart-template.md
├── iotstack-install/
│   ├── SKILL.md
│   └── README.md
├── homey-node-red/
│   ├── SKILL.md
│   └── README.md
├── iot-dehumidification/
│   ├── SKILL.md
│   └── README.md
├── n8n-slack-expert/
│   ├── SKILL.md
│   └── README.md
└── grafana-energy-viz/
    └── SKILL.md
```
