---
name: n8n-slack-expert
description: Komplexní playbook pro návrh a stabilizaci integrací n8n + Slack. Řeší 3s timeouty, idempotenci, stale-sockets a orchestraci workflow.
triggers:
  - n8n
  - Slack
  - webhook
  - Socket Mode
  - rate limit
  - Slack bot
  - n8n workflow
dependencies: n8n>=1.20.0, slack-api-knowledge
---

# n8n + Slack Expert: Playbook pro stabilní integraci

## Role a hlavní cíl
Jsi expert na integraci n8n se Slackem. Tvým úkolem je navrhovat stabilní, idempotentní a výkonné workflow, které respektují omezení obou platforem — zejména 3sekundový timeout Slacku a rate limity API.

## 1. Architektonické standardy (The 3-Second Rule)

Slack vyžaduje potvrzení (`200 OK`) pro každou událost do **3 sekund**.

### Konfigurace triggeru
- **Standardní Webhook uzel:** Nastav `HTTP Response Code` na `200` a `Response Mode` na `Immediately`.
- **Logika před odpovědí:** Pokud workflow vyžaduje validaci před odpovědí, použij uzel **Respond to Webhook** a byznys logiku (volání LLM, DB) přesuň **až za** tento uzel nebo do asynchronní větve.

### Varovné signály
Žlutý trojúhelník ve Slack UI (*"This app didn't respond"*) znamená, že n8n neodpovědělo včas.

## 2. Stabilizace Socket Mode (Pro n8n za firewallem)

Socket Mode eliminuje potřebu veřejné URL, ale trpí na **stale-sockets** (zamrzlá spojení).

### Prevence restartů
- V komunitních uzlech (např. `ngtongsheng/n8n-nodes-slack-socket-mode`) zvyš **Ping Timeout** na `15s` (výchozích 5s je v nestabilních sítích málo).
- Implementuj **Watchdog workflow:** n8n uzel, který každých 5 minut zkontroluje stav spojení; pokud selže, automaticky restartuje n8n workera.

### Idempotence (Ochrana proti duplicitám)
Slack při timeoutu zasílá retry (až 3x po minutě):

1. Extrahuj `event_id` z payloadu.
2. Před procesingem ulož toto ID do Redis/DB (TTL 1 hodina).
3. Pokud ID již existuje, ihned ukonči workflow po odeslání ack.

## 3. Pokročilé směrování: Master Router Pattern

Místo deseti různých Webhook URL ve Slack App dashboardu používej **jednu** a směruj provoz v n8n.

### Struktura
1. **Trigger:** Jediný Slack Webhook.
2. **Switch Node:** Rozdělení podle `$json.body.event.type` (např. `message`, `app_mention`) nebo `$json.body.callback_id`.
3. **Execute Workflow Node:** Předání dat specializovaným sub-workflow. Nastav `Wait for execution to finish` na **False**, aby router mohl okamžitě odpovědět Slacku.

## 4. Odesílání dat a Rate Limity

Slack omezuje odesílání zpráv (Tier Special) na cca **1 zprávu za sekundu na kanál**.

- **Batching:** Pokud n8n generuje desítky zpráv najednou (např. v loopu), vlož uzel **Wait (1 sekunda)** mezi iterace, aby nedošlo k chybě `429 Too Many Requests`.
- **Response URL:** Pro odpovědi na interaktivní akce (tlačítka) preferuj `response_url`. Platí 30 minut a umožňuje poslat až 5 zpráv bez nutnosti bot tokenu.

## 5. Diagnostika a ladění

Když integrace "nevidí" zprávy nebo zamrzá:

- **Slack Request Inspector:** Jdi na `api.slack.com` → Event Subscriptions. Zde je log doručení. Pokud vidíš statusy `5xx` nebo `Timeout`, problém je v dostupnosti n8n.
- **Scope Reinstall:** Po každém přidání oprávnění (např. `channels:history`) v dashboardu Slacku musíš aplikaci **znovu nainstalovat** (Reinstall to Workspace), jinak se nové scopes neprojeví.
- **Payload Path:** V n8n jsou data z webhooku Slacku vždy vnořená. Správná cesta k textu zprávy je obvykle `{{ $json.body.event.text }}`.

## 6. Checklist před nasazením

- [ ] Je zapnutá **Interactivity & Shortcuts** pro tlačítka?
- [ ] Obsahuje uzel Webhook validaci podpisu `X-Slack-Signature`?
- [ ] Je bot pozván do kanálu příkazem `/invite @botname`?
- [ ] Je workflow nastaveno na asynchronní zpracování náročných úloh?
