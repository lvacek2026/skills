# Positrex API — referenční seznam endpointů

Odvozeno z veřejné OpenAPI spec **`https://api2.positrex.eu/v3/api-docs/1-public`**
(OpenAPI 3.0.1). Pro přesná schémata, příklady a další skupiny (`2-full`,
`3-unit-control`) stáhni spec přímo.

- Base URL: `https://api2.positrex.eu`
- Každý request: **HTTP Basic auth** + hlavička **`X-Ptx-Key: <klíč>`**
- Časové údaje: UNIX timestamp v **milisekundách**
- `{id}` / `{clientId}` = cesty parametry

## Veřejné API (`1-public`)

| Metoda | Cesta | Parametry (query) | Popis |
|---|---|---|---|
| GET | `/mobile/user` | — | Přihlášený uživatel (`ApiUser`). |
| GET | `/mobile/user/roles/client/{clientId}` | — | Role uživatele u klienta. |
| GET | `/mobile/user/roles/unit/{id}` | — | Role uživatele u vozidla. |
| GET | `/mobile/client` | — | Klienti (firmy) přihlášeného uživatele. |
| GET | `/mobile/client/{clientId}/unit` | — | Vozidla klienta s aktuálními informacemi. |
| GET | `/mobile/unit/{id}` | — | Informace o vozidle. |
| GET | `/mobile/unit/{id}/positions` | — | Aktuální polohy vozidla. |
| GET | `/mobile/unit/{id}/logbook` | `date` (YYYY-MM-DD), `tps` (bool) | Kniha jízd za jeden den. |
| GET | `/mobile/unit/{id}/logbook-range` | `from`, `to` (YYYY-MM-DD), `tps` (bool) | Kniha jízd za rozsah — **max 7 dní**. |
| GET | `/mobile/unit/{id}/incidents` | — | Incidenty vozidla. |
| GET | `/mobile/unit/{id}/analogue-value` | rozsah — **max 31 dní** | Souhrn analogových hodnot vozidla. |
| GET | `/mobile/unit/{id}/speed` | rozsah — **max 31 dní** | Graf rychlosti vozidla. |

`tps=true` u logbook endpointů naplní u každé jízdy pole `tps` (GeoJSON
FeatureCollection s body trasy — `Point` geometrie, `coordinates` `[lon,lat]`).

## Schémata (`components/schemas` v `1-public`)

`ApiClient`, `ApiCoordinates`, `ApiIncident`, `ApiSummary`, `ApiSummaryPosition`,
`ApiTrip`, `ApiUser`, `Bounds`, `DataSet`, `DataValueDoc`, `Feature`,
`FeatureCollection`, `GeoJsonObject`, `Gps`, `LineString`, `LngLatAlt`,
`MultiLineString`, `MultiPoint`, `MultiPolygon`, `Point`, `Polygon`, `SelectItem`.

### `ApiTrip` (jízda v knize jízd)

| Pole | Typ | Význam |
|---|---|---|
| `id` | integer | ID jízdy |
| `from` / `to` | integer (ms) | začátek / konec |
| `distance` | number | vzdálenost (km) |
| `beginAddress` / `endAddress` | string | adresa odkud / kam |
| `beginOdometer` / `endOdometer` | number | tachometr na začátku / konci |
| `maxSpeed` | integer | max. rychlost (km/h) |
| `tripType` | string | `business` / `private` |
| `driverName` / `driverId` | string / integer | řidič |
| `tps` | FeatureCollection | trasa (jen při `tps=true`) |
| `dayOfStart` | integer (ms) | den začátku |

### unit (vozidlo, z `/mobile/client/{id}/unit`)

`unitId`, `id`, `name`, `registrationPlate`, `objectType`, `objectTypeId`,
`color`, `driverId`, `driverName`, `odometer`, `motoHours`, `lastComm` (ms),
`lastTripType`, `customerId`, `msisdn`, a `lastPosition`:
`{ lat, lon, speed, course, address, lastTp (ms), ioOn, type, accuracy }`.

## Skupiny mimo veřejné API

`/v3/api-docs/2-full` (plná dokumentace) a `/v3/api-docs/3-unit-control`
(servisní / řídicí endpointy) vyžadují autentizaci — stáhni s Basic auth +
`X-Ptx-Key`.
