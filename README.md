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
└── iotstack-install/
    ├── SKILL.md
    └── README.md
```
