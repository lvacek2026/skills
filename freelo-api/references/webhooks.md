# Freelo Webhooks — průvodce

Autoritativní spec: `freelo-webhooks.yaml`. Řešíš webhook? **Vždy si přečti tento soubor + spec**.

## Klíčové principy (must-read)

| Co | Jak |
|---|---|
| Subscribe | `POST /v1/webhooks` (registrace přes REST API se stejnou Basic Auth) |
| Unsubscribe | `DELETE /v1/webhook/{uuid}` |
| Doručení | `POST` na receiver URL, `Content-Type: application/json`, `User-Agent: Freelo webhook` |
| Timeouty | Connect, per-read **a** total: 10 s každý |
| Úspěch | Cokoli `2xx` |
| Retry | Až **10 attempts** total (1 sync + 9 retries, exponential ~300 min) |
| Auto-disable | Po vyčerpání 10 attempts. **Re-enable POUZE z UI** (https://app.freelo.io/settings/webhooks) — žádný API endpoint. |
| Doručení guarantee | **At-least-once** — duplicity očekávej |
| Pořadí | **Negarantováno** — `task_edited` může přijít před `task_created` |
| Dedup | Žádný `event_id`. Použij tuple (`type`, `created_at`, `data.id`) jako dedup key |
| Podpis | **Žádný HMAC, žádný secret, žádný signature.** `User-Agent: Freelo webhook` je trivially forge-able |

### Bezpečnostní pattern: URL = capability

Protože nelze ověřit původ kryptograficky, registruj URL s **dlouhým, nehádatelným tokenem**:

```
https://my-app.example.com/hooks/freelo/a7e1f3c8-9b4d-4e2a-88e7-2f5c9d0b6714
```

- Drž tyto URL mimo logy, public repository, browser history.
- Při kompromitaci: smaž webhook, vytvoř nový s jiným tokenem.

### Timestampy (lišší se od REST API!)

Webhook payloady serializují timestampy v **ISO 8601 / RFC 3339 / ATOM** s **numeric offsetem** (`2026-04-24T15:30:00+02:00`).

**NENÍ normalizováno na UTC** — offset reflektuje TZ producing serveru (typicky Europe/Prague). Použij timezone-aware parser.

(Pro porovnání: REST API posílá *naive ISO8601* bez offsetu — viz `gotchas.md` #1.)

## 11 subscription names (povolené `event_types[]`)

```
task_created
task_edited
task_finished
task_deleted
task_undeleted
task_activated
task_moved
tasklist          ← all lifecycle (created/edited/deleted/archived)
comment           ← all lifecycle (created/edited/deleted) na task i note
note              ← all lifecycle (note = document interně)
workreport        ← all lifecycle
```

`task_edited` se triggeruje při změně: `name`, `due_date`, `due_date_end`, `worker`, `priority_enum`, `tasklist`, custom field value, total time estimate, per-user time estimate.

## Registrační request

```bash
curl -u lukas@viridium.cz:$FREELO_API_KEY \
     -H 'User-Agent: ViridiumIntegration (lukas@viridium.cz)' \
     -H 'Content-Type: application/json' \
     -d '{
       "webhook": {
         "uuid": "550e8400-e29b-41d4-a716-446655440000",
         "event_types": ["task_created","task_finished","comment"],
         "projects_ids": [42, 57],
         "url": "https://my-app.example.com/hooks/freelo/<random-token>"
       }
     }' \
     https://api.freelo.io/v1/webhooks
```

**Pravidla validace:**
- `url` musí začínat `https://` (HTTP odmítnuto 400)
- `url` max 8000 znaků
- `event_types[]` neprázdný; jen z 11 povolených hodnot
- `projects_ids[]` může být prázdný array — pak subscription fungovat jen pro user-scoped events (aktuálně `workreport` only)
- `uuid` volitelné — server vygeneruje v4 UUID a vrátí (idempotency: dodej vlastní UUID pro client-side reproducibility)

Response:
```json
{ "uuid": "550e8400-e29b-41d4-a716-446655440000" }
```

## Envelope formát (společný)

Všechny payloady mají toto:

```json
{
  "type": "task_created",                          // event identifier
  "created_at": "2026-04-24T15:30:00+02:00",       // RFC3339 s offsetem (NENÍ UTC)
  "author": { "id": 12345, "fullname": "Jan Novák" },  // null pro system změny
  "data": { ... }                                  // payload — viz níže
}
```

`author` může být `null` pokud změnu udělal unauthenticated actor (system job, migration).

## Payloady

### `task_*` events (TaskPayload)

```json
{
  "type": "task_created",
  "created_at": "2026-04-24T15:30:00+02:00",
  "author": { "id": 12345, "fullname": "Jan Novák" },
  "data": {
    "id": 9876,
    "name": "Implementovat XYZ",
    "priority_enum": "h",          // h/m/l, nullable
    "due_date": "2026-05-01T09:00:00+02:00",
    "due_date_end": null,
    "date_add": "2026-04-24T15:30:00+02:00",
    "author":   { "id": 12345, "fullname": "Jan Novák" },
    "worker":   { "id": 99, "fullname": "Petr Kolář" },  // nebo null
    "tasklist": { "id": 5, "name": "Backlog", "state": { "id": 1, "state": "active" } },
    "project":  { "id": 42, "name": "Klient X", "state": { "id": 1, "state": "active" } },
    "state":    { "id": 1, "state": "active" },
    "parent_task_id": null,
    "labels":   ["bug", "p1"],
    "custom_fields": [ { ... } ],   // shape závisí na typu CF, accept additional keys
    "total_time_estimate": { "minutes": 480 },  // nebo null
    "users_time_estimates": [
      { "minutes": 240, "user": { "id": 99, "fullname": "Petr Kolář" } }
    ],
    "multi_project_task": {
      "is_multi_project": false,
      "assigned_to": [ { "project": { "id": 42, "name": "Klient X" }, "tasklist": { "id": 5, "name": "Backlog" } } ]
    }
  }
}
```

### `task_moved` (TaskMovedPayload)

Stejný TaskPayload + extra `source` a `target`:

```json
"data": {
  ...TaskPayload...,
  "source": {
    "project":  { "id": 42, "name": "Klient X" },
    "tasklist": { "id": 5,  "name": "Backlog" }
  },
  "target": {
    "project":  { "id": 57, "name": "Klient Y" },
    "tasklist": { "id": 12, "name": "In Progress" }
  }
}
```

`source.project.id`/`source.tasklist.id` mohou být `null` (untyped-nullable v doménovém modelu); názvy projektu mohou být `null` pro projekty bez display name.

### `tasklist` event (TasklistEventEnvelope)

`type` je jeden z `tasklist_created`, `tasklist_edited`, `tasklist_deleted`, `tasklist_archived`.

```json
"data": {
  "id": 5,
  "name": "Backlog",
  "project": { "id": 42, "name": "Klient X", "state": {...} },
  "state": { "id": 1, "state": "active" }
}
```

`tasklist_edited` se triggeruje POUZE při renamu (`name` změna).

### `comment` event (CommentEventEnvelope)

`type`: `comment_created`, `comment_edited`, `comment_deleted`. `data` má dvě varianty:

**Task comment:**
```json
"data": {
  "id": 1234,
  "content": "<p>HTML body</p>",
  "date_add": "2026-04-24T15:30:00+02:00",
  "author": { "id": 12345, "fullname": "..." },
  "project": { "id": 42, "name": "Klient X" },
  "tasklist": { "id": 5, "name": "Backlog", "state": {...} },
  "task": { "id": 9876, "name": "...", "state": {...}, "labels": ["bug","p1"] }
}
```

**Document (note) comment:** klíč je `note`, ne `document`:
```json
"data": {
  "id": 1234,
  "content": "<p>HTML</p>",
  "date_add": "2026-04-24T15:30:00+02:00",
  "author": {...},
  "project": { "id": 42, "name": "Klient X" },
  "note": { "id": 88, "name": "Meeting notes", "state": {...} }
}
```

### `note` event (DocumentEventEnvelope)

Subscription se jmenuje `note` historicky, ale `type` v payloadu používá `document_*`: `document_created`, `document_edited`, `document_deleted`.

```json
"data": {
  "id": 88,
  "name": "Meeting notes",
  "content": "<p>HTML</p>",   // null pokud doc vytvořen bez initial content
  "date_add": "2026-04-24T15:30:00+02:00",
  "author": {...},
  "project": { "id": 42, "name": "Klient X", "state": {...} },
  "state": { "id": 1, "state": "active" }
}
```

### `workreport` event

`type`: `workreport_created`, `workreport_edited`, `workreport_deleted`.

```json
"data": {
  "id": 5555,
  "date_add": "2026-04-24T15:30:00+02:00",
  "date_reported": "2026-04-24T00:00:00+02:00",
  "minutes": 90,
  "cost": { "amount": "150000", "currency": "CZK" },
  "note": "Optional",
  "author": { "id": 12345, "fullname": "..." },
  "project":  { "id": 42, "name": "...", "state": {...} },   // nebo null
  "tasklist": { "id": 5,  "name": "...", "state": {...} },   // nebo null
  "task":     { "id": 9876, "name": "...", "state": {...}, "labels": [...] }  // nebo null
}
```

**Standalone work report** (logged bez přiloženého tasku): `project`, `tasklist`, `task` jsou všechny `null`. `cost.currency` je sentinel `"UNKNOWN"`.

**Pozor:** `workreport_edited` se triggeruje i když se změnil **`budget`**, ale `budget` v payloadu **NENÍ** (jen `cost`). Pokud potřebuješ změnu budgetu detekovat, budeš muset pollovat work report přes REST API.

## Implementace receiveru — minimální skeleton

```python
from datetime import datetime
from flask import Flask, request, abort

app = Flask(__name__)
SEEN = set()  # produkčně: Redis/DB s TTL

@app.post('/hooks/freelo/<token>')
def freelo_hook(token):
    if token != EXPECTED_TOKEN:
        abort(404)  # NEVRACEJ 401/403 — leakuje existenci endpointu
    body = request.get_json(force=True)

    # Dedup
    key = (body.get('type'), body.get('created_at'), body.get('data', {}).get('id'))
    if key in SEEN:
        return ('', 200)  # ACK duplicate
    SEEN.add(key)

    # 200 ASAP, work asynchronně (10s timeout!)
    enqueue(body)
    return ('', 200)
```

**Pravidla pro receivers:**

1. **Vrať 200 do 10 s** — jinak Freelo retryuje a generuje duplicitní eventy. Heavy work udělej asynchronně (queue/worker).
2. **Dedupuj.** Tuple (`type`, `created_at`, `data.id`) jako idempotency key.
3. **Toleruj out-of-order.** Pokud delete přijde před create, drž ve front-loaded queue / reconcile podle `created_at`.
4. **Nikdy nelogguj plné URL** receiveru (to je tvůj secret).
5. **Reconcile přes REST.** Pro stav-of-truth re-fetchni entitu přes REST API — webhook payload je *snapshot v čase*, ne autoritativní stav.

## Dedup snippet

```python
def dedup_key(envelope: dict) -> tuple:
    """At-least-once → tuple unique pro daný delivery event."""
    return (
        envelope['type'],
        envelope['created_at'],
        envelope.get('data', {}).get('id'),
    )
```

## Re-enable po auto-disable

API endpoint NEEXISTUJE. Uživatel musí ručně:
1. Otevřít https://app.freelo.io/settings/webhooks
2. Najít disabled webhook a re-enable

Doporučení: monitoruj svůj receiver a alert na rostoucí 5xx — předejdi auto-disable.
