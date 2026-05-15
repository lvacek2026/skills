# freelo-api

Claude Code / Cowork skill pro práci s **[Freelo.io](https://www.freelo.io) v1
REST API a webhooky** — projekty, tasklists, tasky, subtasks, komentáře, time
tracking, work reporty, faktury, custom fields, soubory, vyhledávání.

Skill přibalí celý OpenAPI spec (REST API + webhooks) jako autoritativní
referenci, takže model nemusí scrapovat dokumentaci a má po ruce všechny
non-obvious chování zdokumentovaná Freelem v `Behavior notes` sekcích.

## Obsah

- `SKILL.md` — vstupní bod skillu (frontmatter + průvodce + 5 kritických gotchas).
- `references/`
  - `endpoints.md` — kompletní seznam ~95 endpointů (32 resource skupin) s parametry.
  - `webhooks.md` — webhook subscription, payload formát, dedup pattern, security.
  - `recipes.md` — copy-paste curl + Python recepty (auth, paginace, time tracking, custom fields, webhook receiver).
  - `schemas.md` — datové struktury / response shapes.
  - `gotchas.md` — 28 non-obvious chování (timestamp formáty, `worker_id` alias, comment-as-description, `mark-as-invoiced` freeze, smart→simple taskcheck fallback…).
  - `freelo-api.yaml` — kompletní OpenAPI 3.0 spec (autoritativní zdroj, ~6300 řádků).
  - `freelo-webhooks.yaml` — webhook spec (~1000 řádků).

## Instalace

### Claude Code (lokální skills)

```bash
# Z kořene tohoto repa zkopíruj složku skillu do uživatelských skills.
mkdir -p ~/.claude/skills
cp -r freelo-api ~/.claude/skills/
```

Po restartu Claude Code se skill automaticky nabídne při relevantních
dotazech (viz `description` ve frontmatteru).

### Claude Code plugin (sdílený)

Pokud distribuuješ sadu skillů jako plugin, vlož složku `freelo-api/`
do `skills/` adresáře pluginu a publikuj přes plugin marketplace.

## Použití

Skill se spustí automaticky, pokud uživatel zmíní například:

- "potřebuju integraci s Freelo přes API"
- "naskriptuj vytvoření tasku ve Freelu z webhooku"
- "jak mám parsovat timestampy z `api.freelo.io`?"
- "Freelo webhook mi přestal chodit / disabluje se"
- "jak přes API přepnout time tracking na jiný task?"
- "Make/n8n integrace s Freelo, custom field hodnota"

Skill explicitně **nerozjede** pro nesouvisející project-management
nástroje (Asana, Trello, Jira, ClickUp, Notion).

## Klíčové vlastnosti

- **Autoritativní spec přímo v skillu** — `references/freelo-api.yaml` (228 KB)
  a `references/freelo-webhooks.yaml` (33 KB) jsou součástí skillu, takže
  model nepotřebuje fetch a má po ruce všechny `Behavior notes (non-obvious)`
  zdokumentované Freelem (popisy validací, side-effecty, plan-gated chování,
  ACL pravidla).
- **5 top gotchas v SKILL.md** — timestampy nejsou RFC3339, currency
  string × 100, paginace od 0, edit přes POST, skryté side-effecty.
- **Plný gotchas katalog (28 položek)** — `worker_id` alias hack, první
  komentář se stane description, `GET /public-link` link vytvoří, smart
  taskcheck silent fallback, snake/camelCase mismatch v custom fields,
  `mark-as-invoiced` freeze work reportů a další.
- **Ready-to-use recepty** — Python helpery pro správné parsování naive
  Europe/Prague timestampů; webhook receiver skeleton s dedup pattern
  (Freelo nepodepisuje payloady a doručuje at-least-once bez `event_id`).

## Zdroje

- Swagger UI: <https://api.freelo.io/docs/v1/freelo-api>
- Webhook help (CZ): <https://www.freelo.io/cs/napoveda/webhooky>
- Webhook help (EN): <https://www.freelo.io/en/help/webhooks>
- API key: <https://app.freelo.io/profil/nastaveni>
- Webhook management UI: <https://app.freelo.io/settings/webhooks>
