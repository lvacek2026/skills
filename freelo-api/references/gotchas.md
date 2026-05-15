# Freelo API — gotchas & non-obvious behavior

Vše, co tě v API dokumentaci přejde dvakrát. Tahle věci jsou v `freelo-api.yaml` v sekcích `Behavior notes (non-obvious)` jednotlivých endpointů — sumarizováno tady.

## 0. n8n 2.x integrace — draft vs published, SQLite WAL

Když Freelo nody v n8n workflow nereagují (workflow běží, ale konkrétní node se tiše neprovede):

- **n8n 2.x rozděluje workflow na "draft" a "published"** — `workflow_entity.versionId` = draft, `activeVersionId` = published. Runtime používá published, ne draft. `import:workflow` přidá nodes do drafta a deaktivuje workflow.
- **Správně:** `n8n publish:workflow --id=<id> --versionId=<new_version_id>` + restart kontejneru. V logu hledej `Processed N draft workflows, M published workflows.` — `M=0` znamená, že nic není reálně nasazeno.
- **Nikdy nepatchuj SQLite DB přímo** (`database.sqlite`) bez správného handle WAL souborů — patche se ztratí (přepsány z WAL) a po pár pokusech se DB **zkorumpuje** (`database disk image is malformed`).
- Před debugem v CLI: vždy nejdříve **n8n UI → Executions → klikni na běh → najdi červené nody**. Z UI rovnou vidíš error message; z CLI ne.

Detail v `recipes.md` → "n8n workflow — řetězení Freelo nodů".

## 1. Timestampy — DVA různé formáty (REST × webhook)

### REST API (request + response)

**Naive ISO8601 bez timezone designátoru** v Europe/Prague (CET/CEST, observuje DST).
Příklad: `2026-04-24T11:12:38`.

**To NENÍ RFC3339-compliant.** Strict parser jako Go `time.Parse(time.RFC3339, ...)` selže.

Doporučený postup:
- Go: parse layout `"2006-01-02T15:04:05"`, pak attach `time.LoadLocation("Europe/Prague")`
- Python: `datetime.fromisoformat(s).replace(tzinfo=ZoneInfo("Europe/Prague"))`
- JS: parse jako naive a manuálně doplň offset (luxon/dayjs s timezone pluginem)

**Send v requestech ve stejném naive formátu Europe/Prague.**

### Webhook payloady

**ISO 8601 / RFC 3339 / ATOM s numeric offsetem** — `2026-04-24T15:30:00+02:00`.
**NENÍ normalizováno na UTC** — offset reflektuje časovou zónu producing serveru.
Použij timezone-aware parser.

### Out-of-office DELETE/POST

`/user/{id}/out-of-office` POST takes `date_from`/`date_to` jako naive Europe/Prague, ale dokumentace tvrdí *"Dates are stored normalized to UTC."* — tedy uloženo v UTC, vraceno v naive Europe/Prague. Pozor při zaokrouhlování.

## 2. Měna — string × 100 ("currency amount")

**Vždy stringy, **vždy** přesně 2 desetinná místa, **vždy** vynásobené 100, **bez** oddělovačů.**

| Lidsky | API |
|---|---|
| `1` | `"100"` |
| `1,000` | `"100000"` |
| `1,000.25` | `"100025"` |
| `0.50` | `"50"` |

Měny: CZK, EUR, USD. Ve webhook payloadu work reportu může být sentinel `"UNKNOWN"` pokud report není připojený k projektu.

## 3. Edit používá POST (ne PUT/PATCH)

Týká se mj.: `POST /task/{id}` (edit), `POST /comment/{id}` (edit), `POST /work-reports/{id}` (edit), `POST /note/{id}` (edit), `POST /project-labels/{id}` (edit).

Důvod: historický REST tvar.

## 4. `worker_id` je tichý alias pro `worker` (task edit)

V `POST /task/{task_id}` (edit) je `worker_id` v request body tiše namapováno na `worker`. Toto je **make.com-compatibility hack**. Funkčně identické, ale undocumented mimo YAML.

```json
{ "worker_id": 42 }   // funguje stejně jako
{ "worker": 42 }
```

## 5. Tracking users — 3 mutually-exclusive shapes

V `POST /task/{task_id}`:
- `tracking_users_ids: [1,2]` — **REPLACE** celý set. Pro vyčištění pošli `[]`.
- `add_tracking_users_ids: [3]` — **MERGE** do existujícího setu.
- `remove_tracking_users_ids: [1]` — **REMOVE** z existujícího setu.

Mixování `tracking_users_ids` (replace) s add/remove v jednom callu je akceptováno, ale výsledek závisí na pořadí operací serveru — **drž jeden mode per call**.

## 6. První komentář na tasku se stane DESCRIPTION

`POST /task/{task_id}/comments`: pokud task **nemá komentáře**, první call vytvoří **description** (interně `is_description=true`), ne regulární komentář. Druhý a další komentáře už jsou normální.

Pokud chceš deterministicky description, použij `POST /task/{task_id}/description` (upsert — replace celé description).

## 7. `GET /public-link/task/{id}` POTICHU VYTVOŘÍ link

GET, který má side-effect: pokud public link na task neexistuje, **vytvoří se** a vrátí. Druhý call vrátí stejný URL.

Pro rotaci: `DELETE` + `GET` (vznikne nový URL).

## 8. Smart taskcheck → simple taskcheck silent fallback

`POST /task/{task_id}/subtasks` se nejprve pokusí o **smart taskcheck** (worker, due_date, tracking_users). Pokud parent není eligible (např. už je smart taskcheck, nebo multi-project parent), server **catchne** `SmartTaskcheckCanNotBeCreatedException` a tiše vytvoří **simple taskcheck** (jen `name`). Extra fields jako `worker`, `due_date`, `tracking_users_ids` se zahodí.

Pokud potřebuješ deterministické chování, **ověř parent eligibility nejdřív**.

## 9. Custom Field endpoints — snake_case × camelCase mismatch

| Endpoint | Klíč v body |
|---|---|
| `/custom-field/add-or-edit-value` (scalar) | `custom_field_uuid` (snake_case) |
| `/custom-field/add-or-edit-enum-value` | `customFieldUuid` (camelCase!) |

Response wrapper:
- Scalar: `{ "custom_field_value": {...} }`
- Enum: `{ "customFieldEnum": {...} }`

Důvod: matching server's internal data key.

## 10. Project Labels add-to-project: ID overrides everything

`POST /project-labels/add-to-project/{projectId}` má dva módy:
- **Mode-A (ID):** pošli `{"id": 123}` — `name`/`color`/`is_private` jsou IGNORED i když pošleš.
- **Mode-B (data):** pošli `{"name": "...", "is_private": true, "color": "#abc"}` — fetch-or-create podle (owner+name+is_private).

```json
// Toto NENÍ rename:
{"id": 123, "name": "typo", "color": "#ff0000"}
// → připojí label 123, ignoruje name+color
```

## 11. Task Labels remove: name-only mode je AGRESIVNÍ

`POST /task-labels/remove-from-task/{task_id}` má 3 módy per-label:
- UUID — přesné
- **name only** — odstraní VŠECHNY labely toho jména, **bez ohledu na color** (může smazat víc labelů!)
- name+color — přesné

Pro precision use UUID nebo name+color.

## 12. Task labels matching je CASE-SENSITIVE

V `POST /task-labels/add-to-task/{task_id}` (name+color mode): `"bug"` a `"Bug"` jsou rozdílné labely. Pozor.

## 13. `/timetracking/start` — pouze 1 session per user

Druhý start na běžící session = **HTTP 409 Conflict** s `"Timetracking is already running."` Použij `/timetracking/edit` pro switch tasku, ne stop+start.

`/timetracking/stop` a `/timetracking/edit` na žádný session = **409 Conflict** s `"Timetracking is not running."`.

## 14. `/task/{id}/activate` — NENÍ symetrické s projektem

Project `/activate` umí unarchive **i** undelete. Task `/activate`:
- Active → no-op (200)
- Finished → reactivate (200)
- **Deleted → 404** (nelze undelete přes API!)

## 15. Cross-project move — `multi_project_task.source_tasklist_id` matters

`POST /task/{task_id}/move/{tasklist_id}` u multi-project tasku:
- **bez** `multi_project_task.source_tasklist_id` (nebo s primárním tasklistem) → cross-project move s aplikací `work_reports_action` / `custom_fields_action`
- **s** child tasklistem → pouze ten child se přesune **v rámci svého projektu**, `work_reports_action` / `custom_fields_action` jsou **IGNOROVÁNY**

## 16. `mark-as-invoiced` je nereverzibilní + freezne work reporty

`POST /issued-invoice/{id}/mark-as-invoiced`: po tomto API call:
- nelze vzít zpět přes API
- underlying work reports se **freeznou** — edit/delete na ně může být odmítnut

Mark až když máš jistotu, že externí účetní systém invoice opravdu vydal.

## 17. `/all-tasks` — `with_label` je deprecated alias

`with_label` (single string) je legacy alias `with_labels[]` (array). Když oba pošleš, `with_label` se merge do `with_labels[]`. Preferuj `with_labels[]`.

## 18. `/work-reports` `with_own_taskless=true` IMPLICITNĚ omezí na callera

Tento parametr automaticky přidá callera do `users_ids[]`. Nelze tímto získat taskless reporty jiných uživatelů.

`currency` defaultuje na `CZK` — pokud mícháš měny, **vždy explicit pass**.

## 19. `tasks_labels[]` filtr ve `/work-reports` chce UUIDs

Ne jména, ne IDs. UUIDs labelů.

## 20. Project Labels delete je HARD-DELETE GLOBÁLNÍ

`DELETE /project-labels/{labelId}` smaže label **ze všech projektů + smaže entity**. Pro detach od jednoho projektu: `POST /project-labels/remove-from-project/{projectId}`.

## 21. Notes/Documents: shared storage

`/note/*` paths jsou interní aliasy `/document/*`. Webhook subscription se jmenuje `note`, ale payload `type` má `document_*`. `name` = title, `content` = body.

`DELETE /note/{id}` vrací **Note shape** (ne SuccessResponse) — quirk pro confirm.

## 22. Search — POST místo GET

`/search` je POST kvůli komplexním JSON filterům (Elasticsearch). `search_query` je **povinné**. Pro filter-only queries (bez textu) použij tag-specifické list endpointy (`/all-tasks`).

`state_ids` defaultuje na `["active"]` — pro archived/finished/template **explicit pass**.

Limit query length → 400 `ElasticsearchQueryLengthExceededException`.

## 23. Webhooks — bez podpisu, deliver at-least-once, nesmí spoléhat na pořadí

Detail v `webhooks.md`. Krátce:
- Žádný HMAC, žádný shared secret. **URL = capability** (zařaď nehádatelný token do URL path).
- 10 s connect/read/total timeout. Non-2xx = failure.
- Až 10 attempts (1 sync + 9 retries) → po vyčerpání je webhook auto-disabled, nutno re-enable z UI.
- **Žádný `event_id`** — dedupe sám podle (`type`, `created_at`, `data.id`).
- **Pořadí není garantováno.** `task_edited` může přijít dřív než `task_created`.
- `workreport_edited` se triggeruje i při změně `budget`, ale `budget` v payloadu **NENÍ** (pouze `cost`).

## 24. `/file/upload` nepřipojuje nikam

POST jen vrátí UUID. Pro přiložení do komentáře:

```html
<a data-freelo-uuid="{uuid}">Caption</a>
```

V task description / comment endpointech máš pak `files[]` s `download_url` (FileUpload schema) — to je zase **jiný shape** (URL-based attach pro externí soubory).

## 25. Validation 400 chyby často jako `UserVisibleErrorMessage` — text je v češtině

Některé 400/409 chybové hlášky jsou české (jak by je viděl user v UI). Nepokoušej se je parsovat regexem na fixed strings; loguj je raw a fail-fast.

Příklady:
- `"Custom field is in the different project than the task."`
- `"Timetracking is already running."`
- `"Timetracking is not running."`
- `"Enum was not found."`
- `"At least one of the following fields must be filled: emails, users_ids"`
- `"Unsupported color (X) provided."`

## 26. Plan limity → `PlanExceededException`

Některé endpointy můžou selhat na plan limitu i když by jinak prošly:
- `POST /project/{id}/activate` (restoring counts vůči project capu)
- `POST /custom-field/create/{project_id}`
- `POST /users/manage-workers` (user seat limit)

HTTP code typicky 402 nebo 429 s `UserVisibleErrorMessage`. Není to retryable bez upgradu plánu.

## 27. ACL filtering je SILENT

Mnoho list endpointů (`/all-tasks`, `/events`, `/all-comments`, `/tasks/relations`, ...) tiše vyfiltruje entity, ke kterým caller nemá přístup. Žádný 403 per-item, žádný marker. Pokud čekáš X items a dostaneš X-3, **ne není to bug** — je to ACL.

## 28. `events_types[]` discoverable přes `/events-types`

Tento endpoint NENÍ v public OpenAPI specu, ale router ho má (`Events:findTypes`). Když potřebuješ valid hodnoty `events_types[]`, zkus zavolat `GET /events-types` (může vyžadovat auth).
