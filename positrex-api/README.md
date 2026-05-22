# positrex-api

Skill pro Claude Code — práce s veřejným REST API služby **Positrex** (GPS
sledování vozidel, elektronická kniha jízd, vozový park).

```bash
npx skills add https://github.com/lvacek2026/skills --skill positrex-api -g
```

## Co skill umí

- Vysvětlí **autentizační model** Positrexu — HTTP Basic auth + hlavička
  `X-Ptx-Key` (není to Bearer token ani certifikát).
- Poskytne referenční **seznam endpointů** `/mobile/...` (`references/endpoints.md`)
  a popis datových schémat (unit, `ApiTrip`, `ApiClient`, `ApiUser`).
- Nasměruje na **veřejnou OpenAPI spec** `/v3/api-docs/1-public`.

## Zdroj dat

Veřejná OpenAPI 3.0.1 spec na `https://api2.positrex.eu/v3/api-docs/1-public`
(bez autentizace). Skupiny `2-full` a `3-unit-control` vyžadují přihlášení.
