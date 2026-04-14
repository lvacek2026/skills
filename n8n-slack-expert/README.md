# n8n + Slack Expert Skill

Claude Code skill pro návrh a stabilizaci integrací n8n se Slackem.

## Instalace

```
/install-skill lvacek2026/n8n-slack-expert-skill
```

## Co skill umí

- Řeší 3sekundový timeout Slacku správným nastavením Webhook uzlů
- Stabilizuje Socket Mode (stale-sockets, watchdog, ping timeout)
- Implementuje idempotenci proti duplicitním retry zprávám
- Navrhuje Master Router Pattern pro centrální směrování událostí
- Hlídá Slack rate limity (batching, response URL)
- Poskytuje diagnostický checklist pro ladění integrace
