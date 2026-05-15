# Freelo API — datové struktury (response shapes)

Stručný přehled klíčových schémat. Plné definice s **všemi** poli v `freelo-api.yaml` (sekce `components.schemas`, řádky cca 4845+).

## Společné primitives

### SuccessResponse
```json
{ "result": "success" }
```

### ErrorResponse
```json
{ "errors": ["Error message."] }
```
Texty někdy česky (UserVisibleErrorMessage).

### PaginatedResponse
Wrapper kolem `data.<resource_name>` array:
```json
{
  "total": 123,
  "count": 100,           // počet items na této stránce
  "page": 0,              // aktuální (od 0)
  "per_page": 100,
  "data": {
    "<resource>": [ ... ]   // např. "tasks", "projects", "comments", "items"
  }
}
```

### Currency
```json
{ "amount": "100025", "currency": "CZK" }   // = 1000.25 CZK
```
Měny: `CZK`, `EUR`, `USD`. Webhook může mít sentinel `"UNKNOWN"`.

### State
```json
{ "id": 1, "state": "active" }
// state ∈ active(1) | archived(2) | finished | deleted | template(3)
```

### UserBasic
```json
{ "id": 12345, "fullname": "Jan Novák" }
```

## Project

### ProjectBasic
`{ id, name }`

### ProjectWithTasklists (ProjectBasic +)
```json
{
  "id": 42, "name": "Klient X",
  "date_add": "2026-04-24T11:12:38",     // naive Europe/Prague
  "date_edited_at": "2026-04-24T11:12:38",
  "tasklists": [{ "id": 5, "name": "Backlog" }],
  "client": { "id": 7, "email": "...", "name": "...", "company": "...", "company_id": "...", "company_tax_id": "...", "street": "...", "town": "...", "zip": "..." }
}
```

### ProjectFull (ProjectWithTasklists + budget data)
Přidává `owner`, `state`, `minutes_budget`, `budget` (Currency), `real_minutes_spent`, `real_cost` (Currency).

### ProjectDetail (ProjectFull + nested tasks/workers)
Tasklists obsahují vnořené tasky se základními poli (id, name, due_date, due_date_end, worker, parent_task_id) a `workers[]` s `hour_rate` objektem.

## Tasklist

### TasklistBasic
`{ id, name }`

### TasklistWithBudget
TasklistBasic + `budget` (Currency)

### TasklistFull (TasklistBasic +)
Přidává `date_add`, `date_edited_at`, `state`, `project` (with state), `real_minutes_spent`, `budget`, `real_cost`.

### TasklistDetail (TasklistBasic +)
Přidává `project_id`, audit timestampy, `tasks[]` se základními poli.

## Task

### TaskBasic / TaskSummary

```json
{
  "id": 9876,
  "name": "...",
  "date_add": "2026-04-24T11:12:38",
  "date_edited_at": "2026-04-24T11:12:38",
  "due_date": "2026-05-01T17:00:00",      // nullable
  "due_date_end": null,
  "count_comments": 4,
  "count_subtasks": 2,
  "author":  { "id": 12345, "fullname": "..." },
  "worker":  { "id": 99, "fullname": "..." },
  "labels":  [{"uuid": "...", "name": "bug", "color": "#ff5555"}],
  "parent_task_id": null,
  "total_time_estimate": { "minutes": 480 },
  "users_time_estimates": [
    { "minutes": 240, "user": { "id": 99, "fullname": "..." } }
  ]
}
```

### TaskFull (TaskSummary +)
Přidává `state`, `project` (with state), `tasklist` (with state), `custom_fields[]`.

### TaskDetail (own shape, full)
Plný detail z `GET /task/{id}`. Klíčové extra:
- `minutes` — aggregated spent (jen pro non-commandery)
- `priority_enum` — `h`/`m`/`l`
- `cost` (Currency) — jen pro non-commandery
- `comments[]` — array CommentWithFiles
- `tracking_users[]`
- `multi_project_task` block pokud relevant
- `copied_from_task` reference

### TaskCreate (request body)
```json
{
  "name": "required",
  "due_date": "2026-05-01T17:00:00",
  "due_date_end": "2026-05-02T17:00:00",
  "worker": 99,
  "priority_enum": "h",
  "comment": { "content": "<p>Initial description (HTML)</p>" },
  "labels": [{"name": "bug", "color": "#ff5555"}, {"uuid": "..."}],
  "tracking_users_ids": [12345, 99],
  "turn_off_authors_tracking": false,
  "subtasks": [{"name": "..."}, ...]
}
```

### TaskFinished (TaskSummary +)
Přidává `date_finished`, `finished_by`.

## Subtask
Stejné jako TaskSummary + `task_id` (parent), `state`, `project`/`tasklist` with states.

## Labels

### TaskLabel
`{ uuid, name, color }`

### ProjectLabel
`{ id, name, color, is_private, users_id, usage_count, can_be_public, can_be_edited }`

### TaskLabelAddInput (oneOf)
```json
// Mode 1 — UUID
{ "uuid": "550e8400-..." }

// Mode 2 — name + optional color (default #77787a) + optional UUID
{ "name": "bug", "color": "#ff5555", "uuid": "..." }
```

### TaskLabelRemoveInput (oneOf)
```json
// 1: UUID
{ "uuid": "..." }
// 2: name only — AGGRESSIVE (matchne všechny barvy)
{ "name": "bug" }
// 3: name + color — precise
{ "name": "bug", "color": "#ff5555" }
```

## Comment

### Comment (basic)
```json
{
  "id": 1234,
  "content": "<p>HTML</p>",
  "date_add": "2026-04-24T11:12:38",
  "files": [{ "id": 1, "uuid": "...", "filename": "...", "size": 12345 }]
}
```

### CommentWithFiles (Comment +)
Přidává `author`, `is_description` (bool!), `comments_reactions[]`, full `files[]` (FileFull).

### CommentFull (z `/all-comments`)
```json
{
  "id": ..., "uuid": "...",
  "content": "<p>HTML</p>",
  "date_add": "...", "date_edited_at": "...",
  "author": {...},
  "task":     { "id": 9876, "name": "..." },        // null pokud comment je na document/file/link
  "tasklist": {...},
  "project":  {...},
  "document": { "uuid": "...", "name": "..." },     // null pokud na tasku
  "link":     { "uuid": "...", "name": "..." },     // null
  "file":     { "uuid": "..." },                    // null
  "files": [...]
}
```

## File

### FileBasic
`{ id, uuid, filename, size }`

### FileFull (FileBasic +)
Přidává `caption`, `description`, `date_add`, `date_edited_at`, `state`.

### FileUpload (request body schema)
**POZOR — to NENÍ raw upload!** Je to schema pro vložení odkazu na již-uploaded file (viz `files[]` v komentářích / description):
```json
{
  "download_url": "https://...",   // required
  "filename": "screenshot.png"
}
```

Pro raw upload použij `multipart/form-data` POST na `/file/upload`.

### FileItem (z `/all-docs-and-files`)
```json
{
  "uuid": "...", "name": "...",
  "author": {...}, "project": {...},
  "directory_uuid": null,
  "date_add": "...",
  "order": 0,
  "type": "directory|link|file|document",
  "filename": "...", "caption": "...",
  "mime_type": "image/png", "extension": "png",
  "size": 12345,
  "color": "#abc",        // pro directory
  "items_count": 7,       // pro directory
  "link": "https://...",  // pro link
  "link_type": "...",
  "note": "..."
}
```

## Time tracking / Work reports

### WorkReport
```json
{
  "id": 5555,
  "date_add": "2026-04-24T11:12:38",
  "date_reported": "2026-04-24",        // pure date, ne datetime
  "note": "...",
  "minutes": 90,
  "cost": { "amount": "150000", "currency": "CZK" },
  "author": {...},
  "worker": {...},
  "task":   { "id": 9876, "name": "..." }   // nullable
}
```

### WorkReportExtended (WorkReport +)
Přidává `project`, `tasklist`, `work_report_id` (nullable).

### WorkReportFull (z `/work-reports`)
WorkReport + `date_edited_at` + nested objekty s víc detailem (task má `minutes`, `cost`, `labels`, `total_time_estimate`, `users_time_estimates`; project má `labels[]`).

### TimeEstimate / UserTimeEstimate
```json
{ "minutes": 480 }
{ "minutes": 240, "user": {...} }
```

### TaskWork (běžící timetracking item)
```json
{
  "id": 1, "reported": "2026-04-24T15:30:00",
  "minutes": 30, "cost": {...}, "notice": null
}
```

## Custom Fields

### CustomField
```json
{
  "uuid": "...",
  "custom_fields_types_uuid": "...",
  "project_id": 42,
  "author_id": 12345,
  "name": "Client ID",
  "date_add": "...",
  "priority": 0
}
```

### CustomFieldValue (scalar)
```json
{
  "uuid": "...",
  "value": "ACME-2026-0042",
  "date_add": "...", "date_edited_at": null,
  "author_id": 12345,
  "task_id": 9876,
  "custom_field_uuid": "..."
}
```

### CustomFieldEnumValue
```json
{
  "uuid": "...",
  "task_id": 9876,
  "custom_field_uuid": "...",
  "value": "Blocked",
  "date_add": "...", "date_edited_at": null,
  "author_id": 12345
}
```

### CustomFieldEnumOption (z list endpointu)
```json
{
  "enum_uuid": "...",
  "enum_value": "Blocked",
  "custom_field_uuid": "...",
  "custom_field_name": "Status"
}
```

### CustomFieldWithValue (jak je vidět na tasku)
```json
{
  "field_uuid": "...",
  "custom_fields_types_uuid": "...",
  "project_id": 42,
  "name": "Client ID",
  "priority": 0,
  "field_date_add": "...",
  "value_uuid": "...",
  "value_author_id": 12345,
  "value": "ACME-2026-0042",
  "value_date_add": "...",
  "value_date_edited_at": null
}
```

## Search result
```json
{
  "score": 0.85,
  "id": 9876,
  "uuid": "...",        // null pro některé typy
  "name": "...",
  "author_id": 12345,
  "type": "task|subtask|project|tasklist|file|comment",
  "highlight_name":    ["...<em>match</em>..."],
  "highlight_content": ["...<em>match</em>..."],
  "project": {...},
  "tasklist": {...},
  "state": 1,           // raw integer state ID
  "is_smart": true
}
```

## Notification
```json
{
  "id": 12345, "type": "task_finished",
  "date_action": "2026-04-24T11:12:38",
  "author": {...}, "who": {...},
  "is_unread": true, "is_new": true,
  "task": {...},     // nullable
  "tasklist": {...}, "project": {...},
  "comment": { "id": ... },     // nullable
  "document": {...}, "file": {...},
  "more_comments": false,
  "more_users": [...]
}
```

## Event (audit log)
```json
{
  "id": 12345,
  "date_action": "2026-04-24T11:12:38",
  "type": "task_created",   // viz `events_types[]` filtr
  "author": {...}, "who": {...},
  "comment": {...},  "task": {...},  "task_check": {...},
  "tasklist": {...}, "project": {...},
  "document": {...}, "file": {...},
  "due_date": null, "due_date_end": null
}
```

## Note (Document)
```json
{
  "id": 88, "name": "Meeting notes",
  "date_add": "...", "date_edited_at": "...",
  "state": {...}, "content": "<p>HTML</p>",
  "author": {...}, "project": {...},
  "files": [...],     // FileFull[]
  "comments": [...]   // CommentWithFiles[]
}
```

## Invoice

### IssuedInvoice
```json
{
  "id": ..., "date_add": "...",
  "note": null,
  "currency": "CZK",
  "minutes": 480,
  "price": { "amount": "...", "currency": "CZK" },
  "subject": { "company_name": "...", "invoice_url": "..." },
  "inv_items": [
    { "id": 1, "name": "...", "minutes": 60, "price": {...} }
  ]
}
```

### IssuedInvoiceDetail (IssuedInvoice +)
`inv_items[].reports[]` array work-report rows (id, work_report_id, project_name, tasklist_name, name, minutes, price).

## TaskRelation
```json
{
  "type": "blocked_by|blocks|related_to|duplicate_of",
  "related_task_id": 9876,
  "related_task_name": "..."
}
```

## PinnedItem
```json
{ "id": ..., "link": "https://...", "title": "..." }
```

## Hardcoded UUIDs custom field types

```
text: 2f7bfe3a-c950-470e-b910-95b4caf5dc4f
number: b1e56fa9-a97a-429b-8ab4-82bebe58933a
enum: f9729a8f-d340-40e4-b2c0-dc46c37e18ce
```
