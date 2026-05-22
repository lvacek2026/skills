---
name: flexibee-api
description: Working with the FlexiBee / ABRA Flexi accounting system REST API — reading and writing invoices (faktura-vydana/prijata), contacts (adresar), bank records, price lists and other "evidence". Use when integrating Czech accounting (FlexiBee, ABRA Flexi, abra.flexi.cz, demo.flexibee.eu), building/parsing the winstrom XML or JSON envelope, constructing /c/<firma>/<evidence> URLs, writing (condition) filters, or using the spojenet/flexibee (php-abraflexi) PHP library.
---

# FlexiBee / ABRA Flexi REST API

FlexiBee (rebranded **ABRA Flexi**) is a Czech accounting/ERP system with a full REST API.
Every record type ("evidence") is exposed under a uniform URL scheme and can be read and
written in XML or JSON. There is no distinction between "create" and "update" — you POST/PUT
a record and FlexiBee decides based on the identifier.

## 1. Base URL structure

```
https://<host>:5434/c/<firma>/<evidence>/<id>.<format>?<params>
```

- `<host>` — server, e.g. `demo.flexibee.eu`, or a self-hosted instance. Default port `5434`.
- `c` — fixed segment ("companies").
- `<firma>` — company identifier (the URL-safe DB name, e.g. `demo`, `moje-firma`).
- `<evidence>` — record type, e.g. `faktura-vydana`, `adresar`.
- `<id>` — optional; omit for the whole collection.
- `<format>` — optional suffix: `xml`, `json`, `pdf`, `csv`, etc. If omitted, the `Accept` header decides; otherwise HTML.

Special endpoints:
- `GET /c.xml` (or `/c.json`) — list of all companies on the server (each `<company>` has `dbNazev` + `nazev`).
- `/c/<firma>/<evidence>/properties` — field metadata for an evidence.
- `/c/<firma>/<evidence>/$sum` — aggregations.
- `/c/<firma>/evidence-list` — list of all available evidence names.

### Addressing a single record — 3 ways

| Form | Example URL fragment | Meaning |
|------|----------------------|---------|
| Internal numeric ID | `/faktura-vydana/158.xml` | FlexiBee's own primary key |
| By code | `/faktura-vydana/code:VF2-0001.xml` | the document's `kod` field |
| By external ID | `/adresar/ext:ESHOP:42.xml` | your own ID stored alongside the record |

External IDs are the key to idempotent integrations: store `ext:<namespace>:<your_id>` on each
record. On the next sync, posting with the same `ext:` ID **updates** the existing record;
if not found, it is **created**. A record can hold its numeric `id` and one or more `ext:` ids
at the same time.

## 2. Authentication

### HTTP Basic auth (simplest, per request)

```bash
curl -u winstrom:winstrom 'https://demo.flexibee.eu:5434/c/demo/adresar.xml'
```

Credentials may also be embedded in the URL (`https://user:pass@host:5434/...`).

### Session token (recommended for many requests)

```bash
# 1. Log in -> get authSessionId
curl -X POST 'https://host:5434/login-logout/login.json' \
     -d '{"username":"novak","password":"heslo"}'
# response: {"success":true,"authSessionId":"<64-char token>", ...}
```

Then send the token on every request via **any** of:
- Cookie: `authSessionId=<token>`
- Header: `X-authSessionId: <token>`
- Query param: `?authSessionId=<token>` (avoid — logged server-side)

Keep alive with `GET /login-logout/session-keep-alive.js` (~every 60 s); renew via
`GET /login-logout/check`.

> Note: REST **write** access is a licensed feature. A `402 Payment Required` means the
> API/write add-on is not enabled for that instance.

## 3. Formats

| Format | Suffix | Content-Type | Import? |
|--------|--------|--------------|---------|
| XML | `.xml` | `application/xml` | yes |
| JSON | `.json` / `.js` | `application/json` | yes |
| CSV | `.csv` | `text/csv` | yes |
| Excel | `.xls` | `application/ms-excel` | yes |
| DBF | `.dbf` | `application/dbf` | yes |
| ISDOC | `.isdoc` / `.isdocx` | `application/x-isdoc` | yes |
| PDF | `.pdf` | `application/pdf` | no (export only) |
| HTML | `.html` | `text/html` | no |

The URL suffix wins over the `Accept` header for output. For input, set `Content-Type`
to match the body. **Input and output format cannot be mixed in one request.** POST bodies
must be raw XML/JSON — not `multipart/form-data`.

## 4. Reading records

```bash
# one invoice as XML
curl -u u:p 'https://host:5434/c/firma/faktura-vydana/158.xml'

# whole collection as JSON
curl -u u:p 'https://host:5434/c/firma/adresar.json'

# PDF of an invoice
curl -u u:p 'https://host:5434/c/firma/faktura-vydana/158.pdf' -o invoice.pdf
```

### Detail levels (`detail` param)

| Value | Returns |
|-------|---------|
| `id` | only primary key + external ids |
| `summary` | basic fields (`id`, `lastUpdate`, `kod`, `nazev`) — default for **lists** |
| `full` | all fields — default for a **single record** |
| `custom:f1,f2,...` | only the named fields (`id` is always included) |

```
?detail=custom:id,kod,sumCelkem,datVyst,stavUhrK
```
Nested collections take a sub-field list in parentheses:
```
?detail=custom:kod,polozkyFaktury(nazev,cenaMj)
```

`relations` adds linked data (export only): `?relations=vazby,prilohy`.

### Paging

- `limit` — page size. **Default 20.** `limit=0` returns **all** records.
- `start` — number of records to skip (independent of `limit`).
- `add-row-count=true` — adds the total matching count to the response.

```
?limit=50&start=100&add-row-count=true
```

### Sorting

```
?order=datVyst@D          # descending; @A = ascending
?order=nazev@A&order=ic@A # multiple keys, repeat the param
```

## 5. Filtering — the `(condition)` query language

Filters go **inside parentheses in the URL path**, in place of the ID:

```
/c/firma/faktura-vydana/(stavUhrK!='code:stavUhr.uhrazeno' and storno=false).xml
```

The whole `(...)` block must be URL-encoded in real requests.

### Operators

| Operator | Meaning |
|----------|---------|
| `=` `==` `eq` | equals |
| `<>` `!=` `ne` `neq` | not equal |
| `<` `lt`, `<=` `lte`, `>` `gt`, `>=` `gte` | comparison |
| `like 'txt'` | contains substring |
| `like similar 'txt'` | contains, diacritics-insensitive |
| `begins 'x'` / `ends 'x'` | prefix / suffix |
| `between A B` | range, e.g. `castka between 100 500` |
| `in (1,2,3)` | enumeration |
| `is null` / `is not null` | null check |
| `is empty` / `is not empty` | empty check |
| `is true` / `is false` | boolean |

Logical: `and`, `or`, `not`, parentheses for grouping.
Precedence: comparison > `not` > `and` > `or`.

### Functions / dynamic values

- `now()` — current date-time, e.g. `(datSplat < now())` = overdue.
- `currentYear()` — current accounting year.
- `me()` — logged-in username.

### Special filters

- **Related fields** via dot notation: `(firma.skupFir='code:ODBĚRATEL-STANDARD')`.
- **Tags / labels**: `(stitky='code:VIP')`.
- **Tree subtree**: `(in subtree 3)` (add `nonrecursive` to exclude descendants).
- **Validity**: records with `platiOd`/`platiDo` are auto-filtered to the current period; disable with `?filtrovat-platnost=false`.

Examples:
```bash
curl -u u:p \
 'https://host:5434/c/firma/banka/(banka=%27code:SIPO%27%20and%20varSym%20is%20null).xml?detail=custom:id,buc&limit=0'

curl -u u:p \
 'https://host:5434/c/firma/faktura-vydana/(ic=%2712345678%27%20and%20storno=false).xml'
```

## 6. Writing records (create / update)

There is **no separate create vs. update**. POST or PUT (FlexiBee treats them identically)
a record to the **collection URL**:
- record with a numeric `id` → must exist, gets **updated**.
- record with only an `ext:` id (or no id) → created if not found, else updated.

### The `winstrom` envelope (XML)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<winstrom version="1.0">
  <faktura-vydana>
    <id>ext:ESHOP:1042</id>           <!-- your external id -->
    <typDokl>code:FAKTURA</typDokl>
    <firma>code:CUSTOMER-1</firma>     <!-- or numeric id, or ext: -->
    <datVyst>2026-01-15</datVyst>
    <datSplat>2026-01-29</datSplat>
    <duzpPuv>2026-01-15</duzpPuv>
    <bezPolozek>false</bezPolozek>
    <polozkyFaktury>
      <faktura-vydana-polozka>
        <nazev>Internet leden 2026</nazev>
        <mnozMj>1</mnozMj>
        <cenaMj>500</cenaMj>
        <typCenyDphK>typCeny.bezDph</typCenyDphK>
        <typSzbDphK>typSzbDph.dphZakl</typSzbDphK>
      </faktura-vydana-polozka>
    </polozkyFaktury>
  </faktura-vydana>
</winstrom>
```

```bash
curl -u u:p -X PUT 'https://host:5434/c/firma/faktura-vydana.xml' \
     -H 'Content-Type: application/xml' --data-binary @invoice.xml
```

You can put **multiple records** (even of different evidences) inside one `<winstrom>` for a
single atomic batch request.

### JSON equivalent

```json
{
  "winstrom": {
    "faktura-vydana": {
      "id": "ext:ESHOP:1042",
      "typDokl": "code:FAKTURA",
      "firma": "code:CUSTOMER-1",
      "datVyst": "2026-01-15",
      "datSplat": "2026-01-29"
    }
  }
}
```
For several records of the same evidence, use a JSON array as the value of `"faktura-vydana"`.

### Field value conventions

- **Code reference**: `code:XXX` points to a codebook entry by its `kód`.
- **External reference**: `ext:NS:ID`.
- **Dates**: `YYYY-MM-DD`.
- **Booleans**: `true` / `false`.
- **Sub-evidence** (line items, payments) nests inside the parent record.

### Attribute modifiers on XML elements

- `removeAll="true"` on a collection element → replace its contents instead of merging
  (e.g. on `<stitky>` to overwrite tags rather than append).
- `<id>` element may appear twice — once numeric, once `ext:` — to set both.

### Actions (`@action` / sub-elements)

Some evidences support operations beyond field updates — e.g. paying an invoice by adding a
nested `<hotovostni-uhrada>` (cash payment) child. Workflow/state actions are exposed per
evidence; check `/properties` or the evidence docs for available actions and their names.

### Dry-run (test save)

Add `?dry-run=true` — FlexiBee runs all validations and returns the result **without saving**.
Invaluable before a real batch import.

### Deleting

```bash
curl -u u:p -X DELETE 'https://host:5434/c/firma/faktura-vydana/158.xml'
```
`200` on success, `404` if it does not exist.

## 7. Responses & error handling

A successful write returns a `<winstrom>` with `<success>true</success>` and a `<results>`
block; created records report their new numeric `id`, and a `request-id` echoing the
identifier you sent (useful to map external ids back to FlexiBee ids). New records also
return a `Location` header.

| HTTP code | Meaning |
|-----------|---------|
| 200 OK | success |
| 201 Created | record created (`Location` header set) |
| 304 Not Modified | unchanged (with `If-Modified-Since`) |
| 400 Bad Request | invalid request / failed PUT |
| 401 Unauthorized | bad/missing credentials |
| 402 Payment Required | REST write access not licensed |
| 403 Forbidden | insufficient permissions / license limit |
| 404 Not Found | evidence or record not found |
| 405 / 406 | method or format not allowed for the resource |
| 500 | server error (no machine-readable body) |

Error bodies (except 500) carry a parseable structure mirroring the write format:
`winstrom > success=false > results > result > errors > error > message` (and a `for`
field naming the offending property). Parse this rather than relying only on the status code.

## 8. Common evidence names

| Evidence | Czech meaning |
|----------|---------------|
| `adresar` | address book / business partners (customers & suppliers) |
| `faktura-vydana` | issued (outgoing) invoice |
| `faktura-prijata` | received (incoming) invoice |
| `faktura-vydana-polozka` | issued-invoice line item (sub-evidence) |
| `pohledavka` | receivable / other receivable |
| `zavazek` | payable / liability |
| `banka` | bank document (transaction) |
| `pokladni-pohyb` | cash-register movement |
| `objednavka-prijata` | received sales order |
| `objednavka-vydana` | issued purchase order |
| `nabidka-vydana` | issued quote/offer |
| `poptavka-prijata` | received inquiry |
| `cenik` | price list / product & service catalogue |
| `skladovy-pohyb` | warehouse movement |
| `sklad` | warehouse |
| `kontakt` | contact person (linked to `adresar`) |
| `ucetni-obdobi` | accounting period |
| `typ-dokladu` | document type codebook |
| `stredisko` | cost centre |
| `zakazka` | job / project |
| `cinnost` | activity codebook |
| `mzdy` | payroll |

Get the authoritative list per instance from `/c/<firma>/evidence-list` and per-evidence
fields from `/c/<firma>/<evidence>/properties`.

### Frequently used fields on `faktura-vydana`

`kod` (number), `typDokl`, `firma`, `varSym` (variable symbol), `specSym`, `datVyst`
(issue date), `datSplat` (due date), `duzpPuv`/`datUcto` (VAT/accounting date),
`sumCelkZakl` (base total), `sumCelkem`/`sumCelkemMen` (grand total), `juhSum`
(amount paid), `zbyvaUhradit` (remaining), `stavUhrK` (payment state, e.g.
`code:stavUhr.uhrazeno`), `formaUhradyCis`/`formaUhrK` (payment method), `storno`,
`bezPolozek` (no-items flag), `stitky` (tags), `popis`, `eanKod`, `polozkyFaktury`.

On `adresar`: `nazev`, `ic` (IČO), `dic` (DIČ/VAT id), `ulice`, `mesto`, `psc`, `email`,
`tel`, `typVztahuK` (relation type, e.g. `typVztahu.odberDodav`), `skupFir` (partner group).

## 9. The `spojenet/flexibee` PHP library (php-abraflexi)

Package: `spojenet/flexibee` on Packagist (`composer require spojenet/flexibee`);
source: github.com/Spoje-NET/php-abraflexi. Requires PHP ^8.1, ext-curl/json/gettext.
(Older, deprecated names: `spoje.net/flexipeehp`, `spoje.net/flexibee`,
upstream `vitexsoftware/php-abraflexi`.)

### Architecture

- Namespace `\AbraFlexi\`.
- Base classes: **`RO`** (read-only) and **`RW`** (read-write).
- Evidence-specific subclasses convert the hyphenated evidence name to CamelCase:
  `faktura-vydana` → `\AbraFlexi\FakturaVydana`, `adresar` → `\AbraFlexi\Adresar`.

### Configuration

Via PHP constants or env vars: `ABRAFLEXI_URL`, `ABRAFLEXI_LOGIN`, `ABRAFLEXI_PASSWORD`,
`ABRAFLEXI_COMPANY`, optionally `ABRAFLEXI_AUTHSESSID`, `ABRAFLEXI_TIMEOUT`,
`ABRAFLEXI_EXCEPTIONS`. Or pass an options array to the constructor:

```php
$invoice = new \AbraFlexi\FakturaVydana(null, [
    'company'  => 'demo',
    'url'      => 'https://demo.flexibee.eu:5434',
    'user'     => 'winstrom',
    'password' => 'winstrom',
]);
```

Constructor options also include `detail`, `filter`, `debug`, `offline`, `timeout`,
`nativeTypes`, `throwException`.

### Reading

```php
// auto-load by id or code: pass it as the first constructor arg
$inv = new \AbraFlexi\FakturaVydana('code:VF2-12345');
$inv = new \AbraFlexi\FakturaVydana(158);

$all   = $inv->getData();                 // all loaded fields
$total = $inv->getDataValue('sumCelkem'); // single field

// collections
$adr   = new \AbraFlexi\Adresar();
$rows  = $adr->getAllFromAbraFlexi();     // fetch many (older API: getColumnsFromFlexibee / loadFromFlexiBee)
```

### Writing

```php
$inv = new \AbraFlexi\FakturaVydana();
$inv->setData([
    'typDokl'  => 'code:FAKTURA',
    'firma'    => 'code:CUSTOMER-1',
    'datVyst'  => new \DateTime(),
    'datSplat' => new \DateTime('+14 days'),
]);
$inv->insertToFlexiBee();  // create; or $inv->sync() to push + reload
```

With `nativeTypes` on, dates come back as `DateTime` objects. `debug => true` validates
before sending. Multiple objects can be chained into one request (batch).

> The exact method names have drifted across library generations (FlexiBee → AbraFlexi
> rename). When in doubt, inspect the installed `vendor/spojenet/flexibee/src` rather than
> assuming — `getData/setData/sync/insertToFlexiBee` are stable; the `*FromFlexibee`
> family was renamed `*FromAbraFlexi`.

## 10. Gotchas

- **POST and PUT are equivalent.** The semantics come entirely from the URL and whether an
  id exists — not from the verb.
- **Create vs. update is implicit.** Use `ext:` external ids to make syncs idempotent and to
  map records back to your own database (read `request-id` and `id` from the response).
- **Default `limit` is 20.** Forgetting it silently truncates result sets. Use `limit=0` to
  get everything (watch memory on large evidences — page with `start` instead).
- **Filters must be URL-encoded** and wrapped in `(...)` in the path. Quote string literals
  with single quotes: `(ic='12345678')`.
- **Validity filtering is on by default** for evidences with `platiOd`/`platiDo` (e.g.
  `cenik`). Add `?filtrovat-platnost=false` to see expired/future records.
- **`code:` vs literal value.** Codebook references need the `code:` prefix; a bare value is
  treated as a literal/id.
- **Input and output format must match** within one request — don't send XML and ask for JSON.
- **POST body must be raw XML/JSON**, never form-encoded / multipart.
- **`402 Payment Required`** ≠ a bug — the instance lacks the REST write license.
- **Always dry-run big imports** (`?dry-run=true`) before committing.
- **Self-hosted instances** often use a self-signed certificate on port 5434 — clients may
  need to disable strict TLS verification (`-k` in curl) in dev.
- **HTTP 500 has no machine-readable body**; all other 4xx errors do — parse the
  `winstrom/results/.../errors/error/message` structure.
- **`removeAll="true"`** is needed on collection elements (e.g. `stitky`) to replace rather
  than merge contents.

## Reference URLs

- Docs hub: https://podpora.flexibee.eu/cs/collections/2592813-dokumentace-rest-api
- URL construction: https://podpora.flexibee.eu/cs/articles/4713911-sestavovani-url
- Authentication: https://podpora.flexibee.eu/cs/articles/4713880-autentizace
- Filtering: https://podpora.flexibee.eu/cs/articles/4722195-filtrovani-zaznamu
- Detail levels: https://podpora.flexibee.eu/cs/articles/4722190-urovne-detailu
- Pagination: https://podpora.flexibee.eu/cs/articles/4722193-strankovani
- HTTP operations: https://podpora.flexibee.eu/cs/articles/4720093-podporovane-http-operace
- Error handling: https://podpora.flexibee.eu/cs/articles/4720060-obsluha-chyb
- Formats: https://podpora.flexibee.eu/cs/articles/4719998-podporovane-formaty
- PHP library: https://github.com/Spoje-NET/php-abraflexi · https://packagist.org/packages/spojenet/flexibee
- Live demo / evidence list: https://demo.flexibee.eu/c/demo/evidence-list
