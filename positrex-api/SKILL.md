---
name: positrex-api
description: Práce s REST API služby Positrex (systems.level.positrex / api2.positrex.eu) — GPS sledování vozidel, kniha jízd, polohy, jízdy, vozidla (units), klienti, řidiči, geozóny, náklady a tankování, notifikace. Spouštěj vždy když uživatel zmíní Positrex, positrex.eu, api2.positrex.eu, eDohled, DFC Monitor, GPS sledování firemních vozidel, elektronickou knihu jízd napojenou na Positrex, integraci Positrexu do jiného systému, nebo když kód importuje volání na `api2.positrex.eu` / cesty `/mobile/...`. NEspouštěj pro nesouvisející GPS/fleet systémy (Webdispečink, Commander, O2 Car Control, Sherlog).
---

# Positrex API skill

Praktický průvodce REST API služby **Positrex** — telematická platforma pro
GPS sledování vozidel, elektronickou knihu jízd a správu vozového parku
(provozovatel: Mobilesoft / systems.level.positrex). Stejné API jede pod více
brandy: Positrex, **eDohled** (Vodafone), **DFC Monitor**, NUTS (Neeco),
Positrex Railway.

> **Autoritativní zdroj:** OpenAPI spec na `https://api2.positrex.eu/v3/api-docs`
> je **za autentizací** (HTTP 401, veřejné `swagger-ui` ukazuje jen prázdný
> petstore stub). Endpointy v tomto skillu jsou odvozené z oficiální mobilní
> appky v3.10.4 (Flutter). Než budeš vymýšlet endpoint, který tu není, **získej
> spec** zavoláním `/v3/api-docs` s platným Bearer tokenem.

Detailní seznam endpointů → **`references/endpoints.md`**.

## Základy

| Vlastnost | Hodnota |
|---|---|
| Base URL (produkce) | `https://api2.positrex.eu` |
| Base URL (test) | `https://testapi.positrex.eu` |
| Legacy host | `https://api.systemgps.eu` |
| Autentizace | `api_key` + login (jméno/heslo) → **Bearer token** v hlavičce `Authorization` |
| Content-Type | `application/json`, UTF-8 |
| Mobilní API | vše pod prefixem `/mobile/...` (to, co volá appka) |
| Číselníky / reseller | pod prefixem `/data/...` |

## Autentizace — NENÍ to klientský certifikát

Časté nedorozumění: Positrex API **nepoužívá klientský certifikát ani mTLS**.
Žádný `.p12` / `.pem` se nikde nezískává ani neinstaluje. Komunikace běží přes
běžné HTTPS (ověřuje se jen *serverový* TLS certifikát) a autentizace je
dvoustupňová:

1. **`api_key`** — per-reseller řetězec identifikující *aplikaci / resellera*,
   ne uživatele. Je to obdoba veřejného „client ID". Sám o sobě **neodemkne
   žádná data** — jen říká serveru, která appka volá.
2. **Login** — POST jména + hesla uživatele (model `LoginCredentials`) spolu
   s `api_key`. Server vrátí **Bearer token** svázaný s daným uživatelským
   účtem. Všechna další volání nesou hlavičku `Authorization: Bearer <token>`.

Přístup k datům je řízen **rolemi uživatele** (`/mobile/user/roles/...`) — token
vidí pouze vozidla klienta, ke kterému má účet oprávnění. `api_key` na tom nic
nemění.

### Login flow (curl)

```bash
# 1) přihlášení → Bearer token   (přesnou cestu/tělo ověř — viz pozn. níže)
curl -sX POST 'https://api2.positrex.eu/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"<user>","password":"<heslo>","apiKey":"<API_KEY>"}'

# 2) autentizovaný request
curl -s 'https://api2.positrex.eu/mobile/client' \
  -H 'Authorization: Bearer <TOKEN>'
```

> ⚠️ **K ověření:** přesná cesta login endpointu a tvar request/response těla
> se z appky nedaly spolehlivě izolovat (Flutter skládá URL za běhu).
> Pravděpodobné kandidáty: `POST /login` nebo `POST /authenticate`. Po prvním
> úspěšném loginu si stáhni `/v3/api-docs` s Bearer tokenem a doplň přesné
> schéma. Token expiruje → počítej s refresh / re-loginem (na HTTP 401
> invaliduj token a přihlas se znovu).

### Jak získat `api_key`

`api_key` je zadrátovaný v každé brandované appce v souboru
`flutter_assets/branding/config.json` (APK/IPA = ZIP, lze rozbalit). Je
**veřejný** — není tajný, sdílí ho všichni uživatelé dané appky:

| Brand | `api_key` | `reseller_id` |
|---|---|---|
| Positrex | `BRQ9VWTYBWDKYDQG` | 1 |
| eDohled (Vodafone) | `HFPWAX3FVKIJFMRD` | 233 |
| DFC Monitor | `DJAP9R8SIXRAOQG3` | 170 |
| NUTS (Neeco) | `Q7GMHEIYZF7U9ICH` | 238 |

**Pro produkční integraci** si vyžádej od podpory Positrexu **vlastní
integrační `api_key`** vázaný na účet/reseller — nezávislost na klíči appky,
oficiálně podporovaná cesta. Appkový klíč použij jen pro vývoj/testy.

## Datový model (hlavní entity)

Z JSON modelů appky (`_$XxxFromJson`):

- **Unit** — vozidlo / sledovaná jednotka. `UnitDetail` = rozšířený detail.
- **Client** — zákazník (firma); uživatel patří jednomu nebo více klientům.
- **Driver** — řidič.
- **Position** — jednotlivá GPS poloha; `Trackpoints` / `TrackpointFeature` =
  GeoJSON body trasy.
- **Trip** — jedna jízda. `LogbookData` = kniha jízd (kolekce jízd za období).
- **Expense** / `OverallExpenses` — náklady; `fuelling` = tankování.
- **Geozone** — geozóna (geofencing).
- **Incident**, `NotificationItem`, `NotificationSettings` — incidenty a notifikace.
- **User**, `LoginCredentials`, `ResellerInfo` — účet, přihlášení, reseller.

## Typický workflow

```
login (api_key + user/heslo) ──► Bearer token
   │
   ├─ GET /mobile/user                       → kdo jsem
   ├─ GET /mobile/client                     → moji klienti (→ clientId)
   ├─ GET /mobile/v1/client/{clientId}/unit  → seznam vozidel
   ├─ GET /mobile/v1/unit/{unitId}/detail    → detail vozidla
   ├─ GET /mobile/unit/{unitId}/positions    → aktuální / historické polohy
   ├─ GET /mobile/v1/unit/{unitId}/logbook-range?from=..&to=..  → kniha jízd
   ├─ GET /mobile/trip/{tripId}              → detail jedné jízdy + trasa
   └─ GET /pdf?from=...                      → PDF export
```

## Gotchas

1. **Není to certifikát.** Viz výše — autentizace je `api_key` + Bearer token.
2. **OpenAPI spec je za autentizací.** `/v3/api-docs` vrací 401 bez tokenu;
   veřejné swagger-ui je prázdný stub. Spec stáhni až s Bearer tokenem.
3. **Token expiruje.** Na HTTP 401 invaliduj cachovaný token a přihlas se znovu
   (jednorázový retry). Token cachuj s TTL, nevolej login před každým requestem.
4. **`api_key` ≠ heslo.** Je veřejný a sdílený; bezpečnost stojí na loginu a
   rolích uživatele, ne na utajení klíče.
5. **Dvě verze unit/logbook endpointů** — `/mobile/unit/{id}/logbook` i
   `/mobile/v1/unit/{id}/logbook(-range)`. Pro knihu jízd za období preferuj
   `v1/.../logbook-range` (parametry `from`/`to`).
6. **Více brandů, jedno API.** eDohled/DFC/NUTS jedou na stejném `api2.positrex.eu`,
   liší se jen `api_key` + `reseller_id`.

## Když uživatel chce konkrétní operaci

| Situace | Kam jít |
|---|---|
| Hledám endpoint pro X | `references/endpoints.md` |
| Detail parametrů / přesná schémata | stáhni `/v3/api-docs` s Bearer tokenem |
| Jak získat API klíč / certifikát | sekce „Autentizace" výše |
