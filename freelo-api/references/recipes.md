# Freelo API — copy-paste recepty

Praktické příklady. Předpokládá:
- `FREELO_EMAIL` = `lukas@viridium.cz`
- `FREELO_API_KEY` v env (z https://app.freelo.io/profil/nastaveni)
- `FREELO_UA = "ViridiumIntegration (lukas@viridium.cz)"` — bez User-Agent API neodpoví

## Bash / curl

### Boilerplate aliasy

```bash
export FREELO_EMAIL="lukas@viridium.cz"
export FREELO_UA="ViridiumIntegration (${FREELO_EMAIL})"
fre() {
  curl -sS -u "${FREELO_EMAIL}:${FREELO_API_KEY}" \
       -H "User-Agent: ${FREELO_UA}" \
       -H 'Content-Type: application/json' \
       "$@"
}
```

### Auth health check

```bash
fre https://api.freelo.io/v1/users/me
# → {"result":"success","user":{"id":12345}}
```

### List všech aktivních projektů (vlastněných)

```bash
fre https://api.freelo.io/v1/projects
```

### Najít projekt podle názvu (paginated search napříč všemi)

```bash
fre 'https://api.freelo.io/v1/all-projects?p=0' | jq '.data.projects[] | select(.name | test("Klient X"; "i"))'
```

### Vytvořit projekt

```bash
fre -X POST https://api.freelo.io/v1/projects \
    -d '{"name":"Nový klient X","currency_iso":"CZK"}'
```

### Vytvořit tasklist v projektu

```bash
PROJECT_ID=42
fre -X POST "https://api.freelo.io/v1/project/${PROJECT_ID}/tasklists" \
    -d '{"name":"Backlog","budget":"100000"}'   # 1000.00 CZK
```

### Vytvořit task (komplexní)

```bash
PROJECT_ID=42
TASKLIST_ID=5
fre -X POST "https://api.freelo.io/v1/project/${PROJECT_ID}/tasklist/${TASKLIST_ID}/tasks" \
    -d '{
      "name": "Implementovat XYZ",
      "due_date": "2026-05-01T17:00:00",
      "priority_enum": "h",
      "worker": 99,
      "labels": [
        {"name": "bug", "color": "#ff5555"},
        {"uuid": "550e8400-e29b-41d4-a716-446655440000"}
      ],
      "tracking_users_ids": [12345, 99],
      "subtasks": [
        {"name": "Navrhnout schéma"},
        {"name": "Implementovat API endpoint", "worker": 99}
      ]
    }'
```

**Pozor:** `due_date` je naive Europe/Prague (žádný `Z`/`+02:00`).

### Edit tasku (přesun na jiného worker, změna priority)

```bash
TASK_ID=9876
fre -X POST "https://api.freelo.io/v1/task/${TASK_ID}" \
    -d '{"worker": 150, "priority_enum": "m"}'
```

### Komentář (pozor — pokud task nemá komentáře, vytvoří DESCRIPTION)

```bash
TASK_ID=9876
fre -X POST "https://api.freelo.io/v1/task/${TASK_ID}/comments" \
    -d '{"content": "<p>Status update: deploy proběhl OK.</p>"}'
```

### Upload souboru a příloha do komentáře

```bash
# 1. Upload (multipart!)
RESP=$(curl -sS -u "${FREELO_EMAIL}:${FREELO_API_KEY}" \
            -H "User-Agent: ${FREELO_UA}" \
            -F "file=@/path/to/screenshot.png" \
            https://api.freelo.io/v1/file/upload)
UUID=$(echo "$RESP" | jq -r .uuid)

# 2. Přiložit do komentáře (HTML inline ref)
fre -X POST "https://api.freelo.io/v1/task/9876/comments" \
    -d "$(jq -n --arg uuid "$UUID" '{
      content: "<p>Screenshot:</p><a data-freelo-uuid=\"\($uuid)\">screenshot.png</a>"
    }')"
```

### Time tracking — start, switch, stop

```bash
# Start na konkrétním tasku
fre -X POST https://api.freelo.io/v1/timetracking/start \
    -d '{"task_id": 9876, "note": "Implementace endpointu"}'

# Switch na jiný task bez ztráty času (edit běžícího session)
fre -X POST https://api.freelo.io/v1/timetracking/edit \
    -d '{"task_id": 1234, "note": "Code review"}'

# Stop → finalizuje work report
fre -X POST https://api.freelo.io/v1/timetracking/stop
```

Při startu na běžícím session: `409 Conflict` `"Timetracking is already running."`

### Logovat work report retroaktivně

```bash
TASK_ID=9876
fre -X POST "https://api.freelo.io/v1/task/${TASK_ID}/work-reports" \
    -d '{
      "minutes": 90,
      "date_reported": "2026-04-23",
      "note": "Pondělní timesheet doplněk"
    }'
```

`cost` se odvodí z hourly rate. Pro custom: `"cost": "150000"` (= 1500.00).

### Vyhledat tasky s labelem napříč projekty

```bash
fre 'https://api.freelo.io/v1/all-tasks?with_labels[]=blocker&state_id=1&p=0' \
    | jq '.data.tasks[] | {id, name, project: .project.name, worker: .worker.fullname}'
```

### Filtrovat work reporty pro fakturaci

```bash
fre 'https://api.freelo.io/v1/work-reports?projects_ids[]=42&date_reported_range[date_from]=2026-04-01&date_reported_range[date_to]=2026-04-30&p=0'
```

### Search (Elasticsearch fulltext)

```bash
fre -X POST https://api.freelo.io/v1/search \
    -d '{
      "search_query": "deploy production",
      "entity_type": "task",
      "state_ids": ["active","finished"],
      "limit": 50
    }'
```

### Custom fields — kompletní flow

```bash
PROJECT_ID=42

# 1. Discover types
fre https://api.freelo.io/v1/custom-field/get-types

# 2. Vytvořit text field
fre -X POST "https://api.freelo.io/v1/custom-field/create/${PROJECT_ID}" \
    -d '{
      "name": "Client ID",
      "type": "2f7bfe3a-c950-470e-b910-95b4caf5dc4f"
    }'
# → vrátí UUID pole

# 3. Set value na tasku (scalar — snake_case!)
fre -X POST https://api.freelo.io/v1/custom-field/add-or-edit-value \
    -d '{
      "custom_field_uuid": "<field-uuid>",
      "task_id": 9876,
      "value": "ACME-2026-0042"
    }'

# 4. Pro enum field (camelCase!)
fre -X POST https://api.freelo.io/v1/custom-field/add-or-edit-enum-value \
    -d '{
      "customFieldUuid": "<field-uuid>",
      "task_id": 9876,
      "value": "<enum-option-uuid>"
    }'
```

### Pozvat externího uživatele do projektu

```bash
fre -X POST https://api.freelo.io/v1/users/manage-workers \
    -d '{
      "projects_ids": [42, 57],
      "emails": ["external@klient.cz"],
      "users_ids": [99]
    }'
```

### Webhook subscription

```bash
fre -X POST https://api.freelo.io/v1/webhooks \
    -d '{
      "webhook": {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "event_types": ["task_created","task_finished","comment","workreport"],
        "projects_ids": [42, 57],
        "url": "https://my-app.example.com/hooks/freelo/a7e1f3c8-9b4d-4e2a-88e7-2f5c9d0b6714"
      }
    }'

# Smazání:
fre -X DELETE https://api.freelo.io/v1/webhook/550e8400-e29b-41d4-a716-446655440000
```

---

## Python (requests)

### Klient s correct timestamp handling

```python
import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

PRAGUE = ZoneInfo("Europe/Prague")
BASE = "https://api.freelo.io/v1"
EMAIL = os.environ["FREELO_EMAIL"]
KEY   = os.environ["FREELO_API_KEY"]
UA    = "ViridiumIntegration (" + EMAIL + ")"

s = requests.Session()
s.auth = (EMAIL, KEY)
s.headers.update({
    "User-Agent": UA,
    "Content-Type": "application/json",
})

def parse_freelo_dt(s: str) -> datetime:
    """Naive ISO8601 z REST API → tz-aware datetime v Europe/Prague."""
    return datetime.fromisoformat(s).replace(tzinfo=PRAGUE)

def format_freelo_dt(dt: datetime) -> str:
    """tz-aware datetime → naive ISO8601 v Europe/Prague pro REST request."""
    return dt.astimezone(PRAGUE).strftime("%Y-%m-%dT%H:%M:%S")

def get(path, **params):
    r = s.get(BASE + path, params=params, timeout=30)
    if r.status_code == 429:
        # rate limit → exponential backoff (caller responsibility)
        raise RuntimeError("rate limited")
    r.raise_for_status()
    return r.json()

def post(path, json=None):
    r = s.post(BASE + path, json=json, timeout=30)
    r.raise_for_status()
    return r.json()
```

### Stránkování přes všechny stránky

```python
def paginate(path, key, **params):
    """Yieldne všechny items napříč stránkami."""
    p = 0
    while True:
        params["p"] = p
        resp = get(path, **params)
        items = resp.get("data", {}).get(key, [])
        if not items:
            return
        for item in items:
            yield item
        # Heuristika: pokud count < per_page → konec
        if resp.get("count", 0) < resp.get("per_page", 100):
            return
        p += 1

# Použití:
for task in paginate("/all-tasks", "tasks", state_id=1):
    print(task["id"], task["name"])
```

### Idempotentní task creator (deduped podle externího ID)

```python
def upsert_task_by_external_id(project_id, tasklist_id, external_id, **fields):
    """
    Pokud task s external_id v custom fieldu existuje, update.
    Jinak create + nastav custom field.
    """
    # Search podle CF — bohužel /all-tasks nefiltruje na CF, takže přes /search:
    search = post("/search", json={
        "search_query": external_id,
        "entity_type": "task",
        "projects_ids": [project_id],
    })
    matches = [it for it in search["data"]["items"] if it.get("type") == "task"]
    if matches:
        task_id = matches[0]["id"]
        return post(f"/task/{task_id}", json=fields)
    return post(f"/project/{project_id}/tasklist/{tasklist_id}/tasks",
                json={"name": fields["name"], **fields})
```

### Webhook receiver (Flask + dedup)

```python
from flask import Flask, request, abort
from datetime import datetime, timedelta

app = Flask(__name__)

# In-memory dedup s TTL — produkčně Redis SET EX 86400
SEEN: dict[tuple, datetime] = {}
DEDUP_TTL = timedelta(hours=24)

EXPECTED_TOKEN = os.environ["FREELO_WEBHOOK_TOKEN"]

@app.post("/hooks/freelo/<token>")
def freelo_hook(token):
    if token != EXPECTED_TOKEN:
        abort(404)
    body = request.get_json(force=True, silent=True) or {}

    # Garbage-collect expired
    now = datetime.utcnow()
    SEEN.update((k, v) for k, v in list(SEEN.items()) if v > now - DEDUP_TTL)

    key = (body.get("type"), body.get("created_at"),
           (body.get("data") or {}).get("id"))
    if key in SEEN:
        return "", 200  # ACK duplicate
    SEEN[key] = now

    # Heavy work asynchronně (10s timeout!)
    enqueue(body)
    return "", 200

def enqueue(body):
    # produkčně: Celery / RQ / SQS
    print(body["type"], body.get("created_at"))
```

### Bulk-vytvoření tasků z CSV

```python
import csv

def bulk_import(csv_path, project_id, tasklist_id):
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            payload = {
                "name": row["name"],
                "due_date": format_freelo_dt(
                    datetime.fromisoformat(row["due_date"]).replace(tzinfo=PRAGUE)
                ) if row.get("due_date") else None,
                "priority_enum": row.get("priority", "m"),
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            try:
                post(f"/project/{project_id}/tasklist/{tasklist_id}/tasks", json=payload)
            except requests.HTTPError as e:
                print(f"FAIL {row['name']}: {e.response.status_code} {e.response.text}")
```

---

## Node-RED / make.com / n8n

### make.com / Integromat
Freelo má oficiální Make app. `worker_id` v task editu je tichý alias na `worker` (přidaný kvůli kompatibilitě s Make).

### n8n

HTTP Request node basics:
- Authentication: **Generic Credential Type → Basic Auth** (uložené credentials s `email` + API key)
- Header: `User-Agent: Your_App_Id (your@email)` — povinné, ale n8n často projde s defaultním axios UA
- Body: JSON, `Content-Type: application/json`
- Pro `POST /task/{id}` (edit) musí být `worker` typu integer (nikoli string). `worker_id` funguje jako alias.

Pro webhook trigger v n8n stačí jakýkoli Webhook node — Freelo POST na něj a parsuj envelope. Dedup pamatuj v separátním uzlu (např. Redis nebo file storage).

#### n8n workflow — řetězení Freelo nodů

Když potřebuješ ID hlavního tasku v pozdějším nodu (např. `Najít` → `Získat podúkoly` → `Odškrtnout` → `Přiřadit nového řešitele`), použij **Set node "Uložit Task ID"** hned po `Najít`. Pak na něj odkazuj přes `$('Uložit Task ID').first().json.mainTaskId`. Reference přes několik HTTP nodů (`$('Najít').item.json...`) občas selhává tiše po výměně credentials nebo formátu odpovědi.

```json
// Set node "Uložit Task ID"
{
  "assignments": [
    {"name": "mainTaskId", "value": "={{ $json.data.tasks.find(t => t.name.toLowerCase().includes('zaúčtovat')).id }}", "type": "number"}
  ]
}

// Pozdější HTTP node URL
"={{ 'https://api.freelo.io/v1/task/' + $('Uložit Task ID').first().json.mainTaskId }}"
```

#### n8n 2.x — kritická gotcha: draft vs published

n8n 2.x má **dvě úrovně workflow** — `versionId` (draft, co edituješ) a `activeVersionId` (published, co reálně běží). Při CLI úpravách:

- `n8n import:workflow --input=wf.json` **deaktivuje** workflow ("Remember to activate later").
- `n8n update:workflow --active=true` je **deprecated** a nestačí — workflow je v DB `active=1`, ale runtime používá staré published version, **nikoli** nově importované nody.
- Správný postup: `n8n publish:workflow --id=<id> --versionId=<new_version_id>` + restart kontejneru.
- Kontroluj log: `Processed N draft workflows, M published workflows.` — pokud `M=0`, žádný workflow se skutečně nespouští, jen jsou registrované triggery na **staré** verzi.

#### NEMANIPULUJ s SQLite DB přímo

n8n 2.x používá **SQLite v WAL módu** (`database.sqlite` + `database.sqlite-wal` + `database.sqlite-shm`). Pokud kopíruješ jen `database.sqlite`:

1. Tvé patche se ztratí — WAL na druhé straně obsahuje starší data co je přepíše.
2. Po několika nesynchronizovaných patchích DB **zkorumpuje** (`database disk image is malformed`).

Pokud opravdu musíš patchovat DB (nedoporučeno), tak:

```bash
docker stop n8n
docker exec n8n_running_helper sqlite3 /home/node/.n8n/database.sqlite "PRAGMA wal_checkpoint(TRUNCATE);"
# nebo PRAGMA journal_mode=DELETE; VACUUM;
rm /home/node/.n8n/database.sqlite-wal /home/node/.n8n/database.sqlite-shm
# pak patch
docker start n8n
```

**Bezpečnější varianta:** edituj v UI (`https://your-n8n/`), nebo používej výhradně `n8n import:workflow` + `n8n publish:workflow`.

#### Tipy pro debug nespouštějícího se nodu

Když HTTP node v řetězci tiše selže (workflow běží, předchozí nody OK, ale tenhle se neprovede):

1. Otevři node v UI a klikni **Execute step** — uvidíš error message v real-time.
2. Zkontroluj v UI **Executions** tabu poslední běh — červené nody mají detail chyby.
3. Ověř export přes CLI:
   ```bash
   docker exec n8n n8n export:workflow --id=<id> --output=/tmp/x.json
   docker cp n8n:/tmp/x.json /tmp/x.json
   ```
   Pokud `jsonBody` má `=` prefix (`"={\"worker_id\":...}"`), n8n to evaluuje jako JS expression a může to selhat. Bez prefixu je to literal string.
4. **NEpoužívej** přímý sqlite patch (viz výše) — runtime cachuje starou verzi.

---

## Časté error paths

| HTTP | Význam | Co dělat |
|---|---|---|
| 400 | Bad request — message často **česky** | Loguj raw body a `errors[]`, ne parse |
| 401 | Špatný email / API key | Ověř přes `/users/me` |
| 403 | ACL — caller nemá rights | Zkontroluj membership v projektu / role |
| 404 | Entity neexistuje **nebo** caller nemá ACL na ni (silent denial) | Často legitimní; nepokoušej se rozlišit |
| 409 | Conflict (timetracking already running, custom field cross-project, ...) | Přečti `errors[]` text |
| 429 | Rate limit | Exponential backoff; nehardcode delay |
| 402/429 | `PlanExceededException` | Upgrade plánu, neretry |
