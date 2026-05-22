---
name: positrex-api
description: Práce s veřejným REST API služby Positrex (api2.positrex.eu) — GPS sledování vozidel, kniha jízd, polohy, vozidla (units), klienti, incidenty. Spouštěj vždy když uživatel zmíní Positrex, positrex.eu, api2.positrex.eu, eDohled, DFC Monitor, GPS sledování firemních vozidel, elektronickou knihu jízd napojenou na Positrex, integraci Positrexu, nebo když kód volá `api2.positrex.eu` / cesty `/mobile/...` s hlavičkou `X-Ptx-Key`. NEspouštěj pro nesouvisející GPS/fleet systémy (Webdispečink, Commander, O2 Car Control, Sherlog).
---

# Positrex API skill

Praktický průvodce **veřejným REST API** služby **Positrex** — telematická
platforma pro GPS sledování vozidel a elektronickou knihu jízd
(provozovatel Mobilesoft). Stejné API jede pod více brandy: Positrex, eDohled
(Vodafone), DFC Monitor, NUTS.

## Zdroj pravdy — OpenAPI spec

Spec je **veřejně dostupná** (bez autentizace):

- `GET https://api2.positrex.eu/v3/api-docs/swagger-config` — seznam doc skupin
- `GET https://api2.positrex.eu/v3/api-docs/1-public` — **veřejné API** (OpenAPI
  3.0.1, ~40 kB) — autoritativní zdroj, čti ho přednostně
- `/v3/api-docs/2-full`, `/v3/api-docs/3-unit-control` — rozšířené skupiny,
  vyžadují autentizaci (servisní/řídicí endpointy)

Než vymyslíš endpoint, který tu není, **stáhni `1-public`** a ověř.
Přehledová tabulka endpointů → `references/endpoints.md`.

## Základy

| Vlastnost | Hodnota |
|---|---|
| Base URL | `https://api2.positrex.eu` |
| Autentizace | **HTTP BASIC** (jméno+heslo web účtu) + hlavička **`X-Ptx-Key`** |
| Mobilní API | vše pod prefixem `/mobile/...` |
| Formát | JSON, UTF-8 |
| Časy | UNIX timestamp v **milisekundách** |
| Rate limit | HTTP 429 při příliš častých dotazech → exponential backoff |

## Autentizace — HTTP Basic + X-Ptx-Key (NENÍ to certifikát ani token)

Z OpenAPI spec (`1-public`, sekce *info*):

> *All mobile endpoints are authenticated using HTTP BASIC authentication.
> All requests require X-Ptx-Key http header. Value for this header shall be
> provided from administrators.*

Takže **každý** request nese:
1. **HTTP Basic auth** — jméno a heslo webového účtu Positrex (účet musí mít
   v portálu dost oprávnění, aby na data viděl).
2. Hlavičku **`X-Ptx-Key: <API klíč>`** — klíč přiděluje administrátor Positrexu
   (nutno si vyžádat; API musí být pro účet povolené).

Žádný Bearer token, žádný login endpoint, žádný klientský certifikát.

### Minimální curl příklad

```bash
curl -s -u 'viridiumAPI:HESLO' \
     -H 'X-Ptx-Key: VAS_API_KLIC' \
     https://api2.positrex.eu/mobile/client
```

Pokud uživatel API klíč / heslo nemá v prostředí, **požádej ho o ně v chatu**.

## Datový model (schémata z `components/schemas`)

- **unit** (vozidlo) — `unitId`/`id`, `name`, `registrationPlate`, `objectType`,
  `driverName`, `odometer`, `lastPosition` (`lat`/`lon`/`speed`/`address`/
  `lastTp`/`ioOn`), `lastTripType`, `customerId`.
- **ApiClient** — `id`, `name`, `timeZoneId`, `mapBounds`, `type`.
- **ApiUser** — `id`, `username`, `firstName`, `lastName`, `email`, `simpleRole`.
- **ApiTrip** (jízda) — `id`, `from`/`to` (ms), `distance` (km),
  `beginAddress`/`endAddress`, `beginOdometer`/`endOdometer`, `maxSpeed`,
  `tripType` (`business`/`private`), `driverName`, `tps` (GeoJSON
  FeatureCollection trasy — naplněné jen při `tps=true`).
- **poloha** — `lat`, `lon`, `speed`, `course`, `address`, `lastTp` (ms), `ioOn`.
- **ApiIncident**, **ApiSummary** (analogové hodnoty / rychlost), GeoJSON typy.

## Typický workflow

```
GET /mobile/user                       → kdo jsem
GET /mobile/client                     → moji klienti (→ clientId)
GET /mobile/client/{clientId}/unit     → vozidla klienta (→ unitId)
GET /mobile/unit/{id}                  → detail vozidla
GET /mobile/unit/{id}/positions        → aktuální polohy
GET /mobile/unit/{id}/logbook-range?from=YYYY-MM-DD&to=YYYY-MM-DD&tps=true
                                       → kniha jízd (vč. trasy)
```

## Gotchas

1. **Auth = Basic + `X-Ptx-Key`.** Bez hlavičky `X-Ptx-Key` vrátí i správné
   jméno/heslo HTTP 401 „Nonexistent user or incorrect password!".
2. **Časy jsou v milisekundách** (UNIX × 1000). Před formátováním děl 1000.
3. **`logbook-range` má limit 7 dní** — větší rozsah → HTTP 400. (`analogue-value`
   a `speed` mají limit 31 dní.)
4. **Trasa jízdy** je v poli `tps` objektu `ApiTrip` jako GeoJSON
   FeatureCollection — naplní se jen s query parametrem `tps=true`. Veřejné API
   **nemá** samostatný `/trip/{id}` endpoint; detail jízdy se bere z logbooku.
5. **Rate limit** — HTTP 429. Necachuj agresivně, ale ani nespamuj.
6. **Více brandů, jedno API** — eDohled/DFC/NUTS jedou na `api2.positrex.eu`,
   liší se jen API klíčem.
7. Souřadnice v GeoJSON jsou `[lon, lat]` (ne `[lat, lon]`).

## Když uživatel chce konkrétní operaci

| Situace | Kam jít |
|---|---|
| Hledám endpoint pro X | `references/endpoints.md` |
| Přesná schémata / parametry / příklady | `GET /v3/api-docs/1-public` (veřejné) |
| Rozšířené (servisní) endpointy | `/v3/api-docs/2-full` — vyžaduje auth |
