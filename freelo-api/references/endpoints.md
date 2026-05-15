# Freelo API — kompletní seznam endpointů

Autoritativní zdroj je `freelo-api.yaml` (a `freelo-webhooks.yaml`). Tato tabulka je rychlý rozcestník — pro plné popisy parametrů, validace a non-obvious chování čti přímo YAML (každý endpoint má vlastní `description` s **Behavior notes**).

## Konvence

- Base URL: `https://api.freelo.io/v1`
- Edit obvykle pomocí `POST` (ne PUT/PATCH)
- Stránkování: `?p=<page>` od 0
- Řazení: `order_by=<col>&order=asc|desc`
- Datum-filtry: `date_range[date_from]=YYYY-MM-DD&date_range[date_to]=YYYY-MM-DD`
- Array param: `?key[]=val1&key[]=val2`

---

## Users

| Method | Path | Účel |
|---|---|---|
| GET | `/users/me` | Auth health check, vrátí `id` přihlášeného uživatele |
| GET | `/users` | Paginated coworkers (sdílí aspoň 1 projekt) |
| GET | `/users/project-manager-of` | Owneři, kteří mě jmenovali svým PM |
| POST | `/users/manage-workers` | Pozvat existující uživatele (`users_ids`) nebo vytvořit nové (`emails`) do projektů (`projects_ids`). Bod `users_ids` vyžaduje neprázdné `projects_ids`. |
| GET | `/user/{user_id}/out-of-office` | OOO status (`null` pokud není pryč) |
| POST | `/user/{user_id}/out-of-office` | Nastavit OOO (`out_of_office.{date_from,date_to}`); přepíše existující |
| DELETE | `/user/{user_id}/out-of-office` | Zrušit OOO |

## Projects

| Method | Path | Účel |
|---|---|---|
| GET | `/projects` | Vlastněné aktivní projekty (FLAT, ne paginated) |
| POST | `/projects` | Vytvořit projekt (`name`, `currency_iso` povinné, volitelně `project_owner_id`) |
| GET | `/all-projects` | Paginated všechny dostupné, filtry: `tags[]` (`"without"` = bez tagů), `states_ids[]` (1=active,2=archived,3=template), `users_ids[]` (owner), `created_in_range` |
| GET | `/invited-projects` | Projekty kde jsem worker (ne owner) |
| GET | `/archived-projects` | Archivované |
| GET | `/template-projects` | Šablony (state=3) |
| GET | `/user/{user_id}/all-projects` | Projekty kde je daný user owner (intersect s mým ACL) |
| GET | `/project/{project_id}` | Detail projektu (tasklisty, budget, real_cost) |
| DELETE | `/project/{project_id}` | Soft-delete |
| GET | `/project/{project_id}/workers` | Paginated workeři projektu |
| POST | `/project/{project_id}/archive` | Archive (idempotent) |
| POST | `/project/{project_id}/activate` | Unarchive **i** undelete (může selhat na PlanExceeded) |
| POST | `/project/{project_id}/remove-workers/by-ids` | `users_ids[]`, all-or-nothing, owner nelze odstranit |
| POST | `/project/{project_id}/remove-workers/by-emails` | `users_emails[]`, all-or-nothing |
| POST | `/project/create-from-template/{template_id}` | Klonovat template; volitelně `name`, `currency_iso`, `project_owner_id`, `preset_date_from`, `users_ids[]` |

## Project Labels (tagy projektů)

| Method | Path | Účel |
|---|---|---|
| GET | `/project-labels/find-available` | Labely dostupné callerovi (private + public z jeho projektů) |
| POST | `/project-labels/{labelId}` | Edit (`name`, `color`, `is_private`) — propaguje se globálně |
| DELETE | `/project-labels/{labelId}` | **Hard-delete globální** (detach od všech projektů + delete entity) |
| POST | `/project-labels/add-to-project/{projectId}` | Připojit label. Mode-A: `id` (ostatní pole IGNORED!). Mode-B: `name`+`is_private` (+optional `color`) → fetch-or-create |
| POST | `/project-labels/remove-from-project/{projectId}` | Stejná dvou-mode logika; bez ID matchuje by name+is_private+owner; 404 pokud label není připojen |

## Pinned Items

| Method | Path | Účel |
|---|---|---|
| GET | `/project/{project_id}/pinned-items` | ACL-filtered seznam pinů (FLAT) |
| POST | `/project/{project_id}/pinned-items` | Pin URL (`link` povinné, `title` volitelné). Idempotent pro vnitřní Freelo URL. |
| DELETE | `/pinned-item/{pinned_item_id}` | Odepnout (target neovlivní) |

## Tasklists

| Method | Path | Účel |
|---|---|---|
| POST | `/project/{project_id}/tasklists` | Vytvořit tasklist (`name` povinné, `budget` jako string×100) |
| GET | `/all-tasklists` | Paginated, filtr `projects_ids[]` |
| GET | `/project/{project_id}/tasklist/{tasklist_id}/assignable-workers` | Kdo může být `worker` na taskách v tomto tasklistu |
| GET | `/tasklist/{tasklist_id}` | Detail tasklistu (project ref, budget, audit timestamps) |
| POST | `/tasklist/create-from-template/{template_id}` | Body: `tasklist_id` (zdroj v template). `target_project_id` volitelné (jinak nový projekt). `target_tasklist_id` volitelné (jinak nový tasklist). `preset_date_from`, `users_ids[]`. |

## Tasks

| Method | Path | Účel |
|---|---|---|
| GET | `/project/{project_id}/tasklist/{tasklist_id}/tasks` | Aktivní tasky v tasklistu (FLAT) |
| POST | `/project/{project_id}/tasklist/{tasklist_id}/tasks` | Vytvořit task (`name` povinné; volitelně `worker`, `due_date`, `due_date_end`, `priority_enum` h/m/l, `comment.content`, `labels[]`, `tracking_users_ids[]`, `turn_off_authors_tracking`, `subtasks[]`) |
| GET | `/all-tasks` | Paginated globální vyhledávání. Filtry: `search_query` (Elasticsearch), `state_id`, `projects_ids[]`, `tasklists_ids[]`, `with_labels[]` (UUIDs nebo jména?), `without_label`, `no_due_date`, `due_date_range`, `finished_overdue`, `finished_date_range`, `worker_id` |
| GET | `/tasklist/{tasklist_id}/finished-tasks` | Paginated finished tasky v tasklistu, volitelně `search_query` |
| POST | `/tasks/relations` | Bulk find relations: `task_ids[]` (1-100). Vrátí `blocked_by`/`blocks`/`related_to`/`duplicate_of`. Plan-gated typy. |
| GET | `/task/{task_id}` | Plný detail tasku |
| POST | `/task/{task_id}` | **Edit** (whitelist: `name`, `worker` (alias `worker_id`!), `due_date`, `due_date_end`, `labels`, `priority_enum`, `tracking_users_ids` (replace), `add_tracking_users_ids` (merge), `remove_tracking_users_ids` (subtract)). Ostatní pole tiše ignorována. |
| DELETE | `/task/{task_id}` | Soft-delete (kaskáduje na subtasky; cannot be undone via /activate) |
| POST | `/task/{task_id}/activate` | Reopen finished task (na deleted task vrací 404 — není symetrické s projektem!) |
| POST | `/task/{task_id}/finish` | Zavřít task (zastaví běžící timetracking pro tento task) |
| POST | `/task/{task_id}/move/{tasklist_id}` | Přesunout task. Body: `work_reports_action` (`move_to_target_project`/`keep_on_origin_project`), `custom_fields_action` (`nothing`/`delete_what_cant_be_keep`/`move_to_comments_what_cant_be_keep`/`delete_all`/`move_to_comments_all`), `multi_project_task.source_tasklist_id` |
| POST | `/task/{task_id}/projects` | Promote na multi-project (UVVP). Body: `tasklist_id` (cílový — projekt se odvodí) |
| GET | `/task/{task_id}/relations` | Relations jednoho tasku |
| DELETE | `/task/{task_id}/projects/{project_id}` | Odebrat task z dalšího projektu (multi-project undo) |
| GET | `/task/{task_id}/description` | Description (= první "pinned" comment) |
| POST | `/task/{task_id}/description` | **Upsert** — replace celé description; `content` + `files[]` (FileUpload by URL) |
| POST | `/task/{task_id}/reminder` | Personal reminder pro callera (`remind_at`); upsert |
| DELETE | `/task/{task_id}/reminder` | Smazat svůj reminder |
| GET | `/public-link/task/{task_id}` | Vrátí public URL — **vytvoří pokud neexistuje!** |
| DELETE | `/public-link/task/{task_id}` | Revoke link |
| POST | `/task/create-from-template/{template_id}` | Body: `task_id` (zdroj), `target_project_id`, `target_tasklist_id`, `preset_date_from`, `users_ids[]` |
| POST | `/task/{task_id}/total-time-estimate` | Upsert total estimate (`minutes`) |
| DELETE | `/task/{task_id}/total-time-estimate` | Smazat total estimate (per-user estimates ZACHOVÁ) |
| POST | `/task/{task_id}/users-time-estimates/{user_id}` | Upsert per-user estimate (`minutes`) |
| DELETE | `/task/{task_id}/users-time-estimates/{user_id}` | Smazat per-user estimate (total nezmění) |

## Subtasks (taskchecks)

| Method | Path | Účel |
|---|---|---|
| GET | `/task/{task_id}/subtasks` | Paginated subtasky |
| POST | `/task/{task_id}/subtasks` | Auto-fallback: nejprve smart taskcheck, při neeligible parent tiše degraduje na simple checklist item (extra fields jako `worker`, `due_date` se ZAHODÍ) |

## Task Labels

| Method | Path | Účel |
|---|---|---|
| POST | `/task-labels` | Bulk-create labelů v workspace; **fetch-or-create** (existující jména reuse) |
| POST | `/task-labels/add-to-task/{task_id}` | Body `labels[]`. Per-label dvě módy: (1) `uuid` only — reuse, (2) `name` (+optional `color` default `#77787a`, `uuid`) → fetch-or-create na **case-sensitive** (name+color) match |
| POST | `/task-labels/remove-from-task/{task_id}` | Body `labels[]`. Tři módy per-label: UUID / name only (AGRESIVNÍ — všechny labely toho jména!) / name+color |

## Comments

| Method | Path | Účel |
|---|---|---|
| POST | `/task/{task_id}/comments` | Vytvořit comment. **Pokud task nemá komentáře, první call vytvoří DESCRIPTION místo komentáře!** Body: `content`, `files[]` (FileUpload) |
| POST | `/comment/{comment_id}` | Edit (replace `content` a `files[]` — ne delta) |
| GET | `/all-comments` | Paginated globální feed. Filtr `type`: `all`/`task`/`document`/`file`/`link`. Default order `date_add desc` |

## Time Tracking

Pouze 1 běžící session per user. 409 Conflict při start (running) / stop+edit (not running).

| Method | Path | Účel |
|---|---|---|
| POST | `/timetracking/start` | Volitelně `task_id` (nullable), `note`. 409 pokud už běží |
| POST | `/timetracking/stop` | Bez body. Vytvoří finalizovaný WorkReport. 409 pokud neběží |
| POST | `/timetracking/edit` | Změnit `task_id` / `note` na běžícím session. Elapsed minutes zachovány |
| GET | `/timetracking/status` | Stav běžícího session |

## Work Reports

| Method | Path | Účel |
|---|---|---|
| GET | `/work-reports` | Paginated. Filtry: `projects_ids[]`, `users_ids[]`, `tasks_ids[]`, `tasks_labels[]` (UUIDs!), `date_reported_range`, `date_add_range`, `date_edited_from`, `with_own_taskless` (auto-omezí na callera!). `currency` default CZK. |
| POST | `/task/{task_id}/work-reports` | Log report (`minutes` povinné; `worker_id` (default caller), `date_reported` (default dnes), `cost` (string×100, default odvozeno z hourly rate), `note`) |
| POST | `/work-reports/{work_report_id}` | Edit (`minutes`, `cost`, `date_reported`, `note`, `task_id` (re-parent)) |
| DELETE | `/work-reports/{work_report_id}` | Delete; freezed po `mark-as-invoiced` |

## Invoicing

| Method | Path | Účel |
|---|---|---|
| GET | `/issued-invoices` | Paginated invoice draft groupy. Filtr `date_range` (po reporting period, ne issued), `projects_ids[]` |
| GET | `/issued-invoice/{invoice_id}` | Detail (total, currency, period, project) |
| GET | `/issued-invoice/{invoice_id}/reports` | **CSV download** (Content-Type text/csv) |
| GET | `/issued-invoice/{invoice_id}/reports-json` | JSON ekvivalent |
| POST | `/issued-invoice/{invoice_id}/mark-as-invoiced` | **Nereverzibilní!** Body: `url`, `subject`. Freezne work reporty. |

## Notifications

| Method | Path | Účel |
|---|---|---|
| GET | `/all-notifications` | Pouze callerovy. Filtry: `projects_ids[]`, `users_ids[]` (autoři), `teams_uuids[]`, `notification_types[]`, `only_unread`. Default order `date_add desc` |
| POST | `/notification/{notification_id}/mark-as-read` | Idempotent |
| POST | `/notification/{notification_id}/mark-as-unread` | Idempotent |

## Events (audit log)

| Method | Path | Účel |
|---|---|---|
| GET | `/events` | Paginated activity feed. Filtry: `projects_ids[]`, `users_ids[]`, `events_types[]`, `tasks_ids[]`, `date_range`, `order`. ACL injectován serverem (filtruje data ven). |

## Files

| Method | Path | Účel |
|---|---|---|
| GET | `/file/{file_uuid}` | Stream raw file (octet-stream) |
| POST | `/file/upload` | **multipart/form-data** s `file`. Max 100 MB. Vrátí `uuid`. NEpřipojuje nikam — UUID si pak referenuj v komentáři jako `<a data-freelo-uuid="{uuid}">` nebo v `files[]` polích |
| GET | `/all-docs-and-files` | Paginated cross-project. Filtr `type`: `directory`/`link`/`file`/`document` |

## States

| Method | Path | Účel |
|---|---|---|
| GET | `/states` | Lookup tabulka (cache aggressively); státy: `active`/`archived`/`finished`/`deleted`/`template` |

## Custom Fields

UUIDs jako primární keys.

| Method | Path | Účel |
|---|---|---|
| GET | `/custom-field/get-types` | Vrátí UUIDy supported typů. Hard-coded: text=`2f7bfe3a-c950-470e-b910-95b4caf5dc4f`, number=`b1e56fa9-a97a-429b-8ab4-82bebe58933a`, enum=`f9729a8f-d340-40e4-b2c0-dc46c37e18ce` |
| POST | `/custom-field/create/{project_id}` | Vyžaduje project commander. Body: `name`, `type` (UUID), volitelně `uuid`. PlanExceeded může vrátit 402/429 |
| POST | `/custom-field/rename/{uuid}` | Pouze `name`; type/uuid immutable |
| DELETE | `/custom-field/delete/{uuid}` | Soft-delete |
| POST | `/custom-field/restore/{uuid}` | Restore |
| POST | `/custom-field/add-or-edit-value` | Upsert SCALAR (text/number) value. Body: `custom_field_uuid` (snake_case!), `task_id`, `value`. Cross-project mismatch → 409 |
| POST | `/custom-field/add-or-edit-enum-value` | Upsert ENUM value. Body: `customFieldUuid` (camelCase!), `task_id`, `value` (UUID enum optionu) |
| DELETE | `/custom-field/delete-value/{uuid}` | Smazat value (history zachováno) |
| GET | `/custom-field-enum/get-for-custom-field/{custom_field_uuid}` | List enum opcí (bez soft-deleted) |
| POST | `/custom-field-enum/create/{custom_field_uuid}` | Body: `value`, volitelně `uuid` |
| POST | `/custom-field-enum/change/{custom_field_enum_uuid}` | Pouze `value` (rename). UUID zachován = task references stále fungují |
| DELETE | `/custom-field-enum/delete/{custom_field_enum_uuid}` | **Bezpečné** — odmítne pokud option v use. Vrací `UserVisibleErrorMessageException` |
| DELETE | `/custom-field-enum/force-delete/{custom_field_enum_uuid}` | **Destruktivní** — vyčistí referencing values na null |
| GET | `/custom-field/find-by-project/{project_id}` | Všechny CF + boolean `is_commander` (pro UI) |

## Notes / Documents

(Note = Document interně; `/note/*` = alias `/document/*`.)

| Method | Path | Účel |
|---|---|---|
| POST | `/project/{project_id}/note` | Vytvořit (`name` povinné, `content`) |
| GET | `/note/{note_id}` | Detail |
| POST | `/note/{note_id}` | Edit (`name`, `content`) — overwrite, žádná history |
| DELETE | `/note/{note_id}` | Soft-delete; vrátí Note shape (ne SuccessResponse — quirk!) |

## Search

| Method | Path | Účel |
|---|---|---|
| POST | `/search` | Body JSON. **`search_query` povinné.** Volitelně: `projects_ids`, `tasklists_ids`, `tasks_ids`, `authors_ids`, `workers_ids`, `state_ids` (default `["active"]`; další: `archived`, `finished`, `template`, `not_template`, `archived_finished`, `archived_unfinished`), `lang`, `due_date.{date_from,date_to}`, `entity_type` (`task`/`subtask`/`project`/`tasklist`/`file`/`comment`), `page` (default 0), `limit` (default 100). Query length limit → 400 ElasticsearchQueryLengthExceeded |

## Webhooks (management)

Detaily v `webhooks.md`.

| Method | Path | Účel |
|---|---|---|
| POST | `/webhooks` | Body: `webhook.{event_types[],projects_ids[],url,uuid?}`. URL musí být `https://`, max 8000 znaků |
| DELETE | `/webhook/{uuid}` | Smazat subscription |
