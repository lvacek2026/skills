# Positrex API — referenční seznam endpointů

Odvozeno z oficiální mobilní appky Positrex **v3.10.4** (Flutter, balíček
`systems.level.positrex`). HTTP metody jsou většinou **odhadnuté** dle REST
konvencí — přesné metody, parametry a schémata ověř proti `/v3/api-docs`
(staženo s platným Bearer tokenem).

- Base URL: `https://api2.positrex.eu` (test: `https://testapi.positrex.eu`)
- Hlavička: `Authorization: Bearer <token>` u všech `/mobile/...`
- `{clientId}`, `{unitId}`, `{tripId}` = cesty parametry (v appce placeholdery `%|n%`)
- Query parametry viděné v appce: `clientId`, `unitId`, `tripId`, `limit`, `offset`, `from`, `to`

## Autentizace

| Metoda | Cesta | Popis |
|---|---|---|
| POST | `/login` *(k ověření)* | Přihlášení: `LoginCredentials` (username, password) + `api_key` → Bearer token. Přesnou cestu/tělo ověř — kandidát i `/authenticate`. |
| GET | `/v3/api-docs` | OpenAPI 3 spec — **vyžaduje Bearer token** (jinak 401). |

## Uživatel (User)

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/mobile/user` | Aktuálně přihlášený uživatel. |
| POST | `/mobile/user/change-password` | Změna hesla. |
| POST | `/mobile/user/reset-password` | Reset hesla. |
| DELETE | `/mobile/user/delete-account` | Smazání účtu. |
| GET | `/mobile/user/roles/client/{clientId}` | Role uživatele vůči klientovi. |
| GET | `/mobile/user/roles/unit/{unitId}` | Role uživatele vůči vozidlu. |

## Klient (Client)

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/mobile/client` | Klienti přihlášeného uživatele. |
| GET | `/mobile/client/{clientId}/driver` | Řidiči klienta. |
| GET | `/mobile/client/{clientId}/geozone` | Geozóny klienta. |
| GET | `/mobile/client/{clientId}/invitation` | Pozvánky. |
| GET | `/mobile/client/{clientId}/link-to-position` | Sdílené odkazy na polohu. |
| GET | `/mobile/client/{clientId}/unconfirmed-contracts` | Nepotvrzené smlouvy. |
| POST | `/mobile/client/confirm-contracts/{id}` | Potvrzení smluv. |
| POST | `/mobile/client/{clientId}/add-unit/{code}` | Přidání vozidla podle kódu. |
| POST | `/mobile/client/{clientId}/add-unit/{code}/complete-client` | Přidání vozidla + dokončení klienta. |

## Vozidla (Unit)

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/mobile/v1/client/{clientId}/unit` | **Seznam vozidel klienta.** |
| GET | `/mobile/unit/{unitId}` | Vozidlo. |
| GET | `/mobile/v1/unit/{unitId}/detail` | **Detail vozidla.** |
| POST | `/mobile/unit/{unitId}/update` | Úprava vozidla (`UnitEditData`). |
| GET | `/mobile/unit/{unitId}/positions` | **GPS polohy vozidla.** |
| GET | `/mobile/unit/{unitId}/logbook` | Kniha jízd vozidla. |
| GET | `/mobile/v1/unit/{unitId}/logbook` | Kniha jízd (v1). |
| GET | `/mobile/v1/unit/{unitId}/logbook-range` | **Kniha jízd za období** (`from`, `to`). |
| GET | `/mobile/unit/{unitId}/available-profiles` | Dostupné profily jízd. |
| POST | `/mobile/unit/{unitId}/request-profile-change` | Žádost o změnu profilu. |
| GET | `/mobile/unit/{unitId}/tank-fullness` | Stav nádrže. |
| GET | `/mobile/unit/{unitId}/analogue-value-order` | Pořadí analogových hodnot. |
| POST | `/mobile/unit/{unitId}/analogue-value-set` | Nastavení analogových hodnot. |
| GET | `/mobile/unit/{unitId}/file` | Soubory vozidla. |
| GET | `/mobile/unit/{unitId}/file/{fileId}` | Konkrétní soubor. |
| GET | `/mobile/unit/{unitId}/expenses` | Náklady vozidla. |
| GET | `/mobile/unit/{unitId}/expenses/sum` | Součet nákladů. |
| GET | `/mobile/unit/{unitId}/fuelling` | Tankování vozidla. |

## Jízdy (Trip)

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/mobile/trip/{tripId}` | Detail jedné jízdy (čas, trasa, řidič, km). |

## Náklady a tankování

| Metoda | Cesta | Popis |
|---|---|---|
| GET/POST | `/mobile/fuelling` | Tankování. |
| GET/POST | `/mobile/other-expenses` | Ostatní náklady. |

## Korekce tachometru (odometer)

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/mobile/correctionOfOdometer/unit/{unitId}` | Korekce tachometru vozidla. |
| GET | `/mobile/correctionOfOdometer/unit/{unitId}/check` | Kontrola korekce. |
| GET | `/mobile/correctionOfOdometer/unit/{unitId}/list` | Seznam korekcí. |

## Geozóny a incidenty

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/mobile/geozone` | Geozóny. |
| GET | `/mobile/incident` | Incidenty. |
| POST | `/mobile/incident/approve` | Schválení incidentu. |
| POST | `/mobile/incident/approve/unit` | Schválení incidentu pro vozidlo. |
| GET | `/mobile/watch-dog/{id}` | Watch-dog (hlídání). |

## Notifikace

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/mobile/notifications` | Notifikace. |
| GET | `/mobile/notifications/list` | Seznam notifikací. |
| GET | `/mobile/notifications/enabled` | Zapnuté notifikace. |
| POST | `/mobile/notifications/set-enabled` | Zapnutí/vypnutí notifikace. |
| POST | `/mobile/notification/register-device` | Registrace zařízení (push / FCM token). |
| GET | `/mobile/created-notification` | Vytvořené notifikace. |
| GET | `/mobile/created-notification/unread` | Nepřečtené. |
| POST | `/mobile/created-notification/mark-read` | Označit jako přečtené. |

## Reseller a číselníky (`/data/...`)

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/data/reseller/info` | Informace o resellerovi. |
| GET | `/data/reseller/link` | Odkazy resellera. |
| GET | `/data/reseller/privacy-policy` | Zásady ochrany soukromí. |
| GET | `/data/reseller/terms` | Obchodní podmínky. |
| GET | `/data/localization` | Lokalizační řetězce. |
| GET | `/data/object-types` | Typy objektů (číselník). |
| GET | `/data/track-orders` | Track orders. |
| GET | `/data/trip-type-variant` | Varianty typu jízdy (soukromá/služební…). |

## Registrace

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/registration/reseller/products` | Produkty resellera. |
| POST | `/registration/register-client` | Registrace nového klienta. |

## Export

| Metoda | Cesta | Popis |
|---|---|---|
| GET | `/pdf?from=...` | PDF export (kniha jízd / report). |
