# positrex-api

Skill pro Claude Code — práce s REST API služby **Positrex** (GPS sledování
vozidel, elektronická kniha jízd, vozový park).

```bash
npx skills add https://github.com/lvacek2026/skills --skill positrex-api -g
```

## Co skill umí

- Vysvětlí **autentizační model** Positrexu (`api_key` + login → Bearer token —
  pozor, **není** to klientský certifikát).
- Poskytne referenční **seznam endpointů** `/mobile/...` a `/data/...`
  (`references/endpoints.md`).
- Popíše datový model (Unit, Trip, Position, LogbookData, Client…) a typický
  workflow integrace.

## Zdroj dat

OpenAPI spec Positrexu je za autentizací. Endpointy v tomto skillu jsou
odvozené z oficiální mobilní appky v3.10.4. Po prvním loginu doporučeno stáhnout
`/v3/api-docs` s Bearer tokenem a doplnit přesná schémata.
