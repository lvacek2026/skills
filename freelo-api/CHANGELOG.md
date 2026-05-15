# Changelog

Všechny významné změny tohoto skillu se zaznamenávají do tohoto souboru.

Formát vychází z [Keep a Changelog](https://keepachangelog.com/cs/1.1.0/)
a verzování dle [SemVer](https://semver.org/lang/cs/).

## [0.1.0] – 2026-05-15

### Added
- Iniciální verze skillu pro Freelo.io v1 API.
- `SKILL.md` — frontmatter s trigger description (Freelo, freelo.io,
  app.freelo.io, api.freelo.io, integrace, Make/n8n/Zapier), explicitní
  exclusion proti Asana/Trello/Jira/ClickUp/Notion. Obsahuje shrnutí
  základů (Basic Auth s emailem + API key, povinný `User-Agent`,
  base URL `https://api.freelo.io/v1/`, JSON UTF-8, `429` backoff)
  a top-5 kritických gotchas.
- `references/freelo-api.yaml` (228 KB) — kompletní OpenAPI 3.0 spec
  staženo z `https://api.freelo.io/docs/v1/freelo-api.yaml`. Obsahuje
  všechny `Behavior notes (non-obvious)` sekce zdokumentované Freelem.
- `references/freelo-webhooks.yaml` (33 KB) — webhook spec.
- `references/endpoints.md` — přehledová tabulka ~95 endpointů ve
  32 resource skupinách (Users, Projects, Project Labels, Pinned Items,
  Tasklists, Tasks, Subtasks, Task Labels, Comments, Time Tracking,
  Work Reports, Invoicing, Notifications, Events, Files, States,
  Custom Fields, Notes/Documents, Search, Webhooks).
- `references/webhooks.md` — webhook subscription flow, 11 event typů,
  envelope/payload struktury, retry policy (10 attempts → auto-disable),
  dedup pattern (at-least-once bez `event_id`), URL-as-capability
  bezpečnostní doporučení.
- `references/recipes.md` — copy-paste curl + Python:
  - Auth health check, search, paginace přes `?p=`.
  - Vytvoření tasku s labely + subtasks + tracking users.
  - Time tracking start/edit/stop flow.
  - Upload souboru (multipart) + příloha do komentáře přes
    `<a data-freelo-uuid="...">` HTML ref.
  - Custom fields kompletní flow (text + enum, snake/camelCase).
  - Webhook receiver (Flask) s dedup tuple
    (`type`, `created_at`, `data.id`).
- `references/schemas.md` — datové struktury (Currency × 100, State,
  TaskBasic/Summary/Full/Detail/Created, Comment/CommentWithFiles/CommentFull,
  WorkReport/Extended/Full, CustomField/Value/EnumValue/EnumOption,
  IssuedInvoice/Detail, hardcoded UUIDs custom field types).
- `references/gotchas.md` — 28 položek non-obvious chování:
  1. Naive ISO8601 Europe/Prague (REST) vs RFC3339+offset (webhooky)
  2. Currency string × 100 ("100025" = 1000.25)
  3. Edit přes POST, ne PUT/PATCH
  4. `worker_id` tichý alias pro `worker` (make.com hack)
  5. Tracking users — 3 mutually-exclusive update shapes
  6. První komentář na tasku se stane DESCRIPTION
  7. `GET /public-link/task/{id}` link VYTVOŘÍ
  8. Smart→simple taskcheck silent fallback
  9. Custom Fields snake_case × camelCase mismatch
  10. Project Labels `id` overrides ostatní pole
  11. Task labels remove `name only` mode AGRESIVNÍ
  12. Task label matching CASE-SENSITIVE
  13. Time tracking 1 session per user, 409 Conflict
  14. `/task/{id}/activate` NENÍ symetrické s projektem
  15. Cross-project move `multi_project_task.source_tasklist_id`
  16. `mark-as-invoiced` freeze + nereverzibilní
  17. `with_label` deprecated
  18. `with_own_taskless` IMPLICIT user filter
  19. `tasks_labels[]` chce UUIDs
  20. Project Labels delete je HARD-DELETE GLOBÁLNÍ
  21. Notes/Documents shared storage; webhook `note` → `document_*`
  22. `/search` POST + `state_ids` default `["active"]`
  23. Webhooks bez signing, at-least-once, no ordering
  24. `/file/upload` nepřipojuje
  25. 400 errory často česky (UserVisibleErrorMessage)
  26. PlanExceededException na restore/create
  27. ACL filtering je SILENT
  28. `events_types[]` discoverable přes `/events-types`

### Notes
- Spec staženo z živého Freelo Swagger UI 2026-05-15.
- Trigger description v SKILL.md cíleně vylučuje konkurenční PM nástroje,
  aby skill nesvícel falešně.
- LICENSE je MIT (přejato ze sister skillů v repu).
