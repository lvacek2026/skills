---
name: zabbix-template-export
description: Tvorba a import Zabbix šablon (templates) napříč verzemi 5.0 až 7.x. Použij vždy, když uživatel zmíní Zabbix šablonu, template, zbx_export, import šablony, `Unsupported import file extension`, `unexpected tag`, `Group ... does not exist`, `Cannot find value map`, `Cannot find host interface`, SNMP template, value map, trigger expression, GETBULK/`tooBig`, nebo když je potřeba vygenerovat XML/YAML šablonu z vlastní MIB či tabulky OID. Skill řeší rozdíly formátu mezi verzemi (YAML až od 5.2, UUID od 6.0, applications vs tagy, stará vs nová syntaxe triggerů, kořenové vs vnořené triggers/graphs/value_maps), postup jak získat autoritativní schéma ze zdrojáků, validaci před importem a typické chyby na straně hosta.
---

# Zabbix šablony — export, import a rozdíly mezi verzemi

Import v Zabbixu hlásí **vždy jen první špatný tag**. Opravovat naslepo proto
znamená kolo pokus-omyl za každou chybu — a když soubor generuješ pro někoho
jiného, čeká u toho. Tenhle skill existuje, aby se šlo rovnou na jistotu.

**Základní pravidlo: nikdy nehádej schéma. Stáhni ho.** Postup je v §2.

## 1. Nejdřív zjisti verzi

Bez přihlášení, `apiinfo.version` autentizaci nevyžaduje:

```bash
curl -s -X POST -H 'Content-Type: application/json-rpc' \
  -d '{"jsonrpc":"2.0","method":"apiinfo.version","params":{},"id":1}' \
  http://<zabbix>/api_jsonrpc.php
```

Formát exportu se mezi verzemi **zásadně** liší. Tabulka je to podstatné:

| Vlastnost | 5.0 | 5.2 | 5.4 | 6.0+ |
|---|---|---|---|---|
| YAML import | **ne** | ano | ano | ano |
| XML import | ano | ano | ano | ano |
| `<uuid>` u objektů | ne | ne | ne | **povinné** |
| Zařazení položek | `applications` | `applications` | tagy | tagy |
| Syntaxe triggerů | `{Tpl:key.last()}` | `{Tpl:key.last()}` | `last(/Tpl/key)` | `last(/Tpl/key)` |
| `triggers`, `graphs`, `value_maps` | **kořen** | kořen | v šabloně | v šabloně |
| Skupiny šablon | host groups | host groups | host groups | `template_groups` |

> Nejčastější omyl: vzít šablonu z internetu psanou pro 6.0 a cpát ji do 5.0.
> Padne hned na první rozdíl a zbytek se neukáže.

## 2. Autoritativní schéma ze zdrojáků

GitHub mirror `zabbix/zabbix` má jen podporované větve (6.0+). Starší verze
jsou na CDN — pozor na `oldstable`, ne `stable`:

```bash
curl -sL -o z.tar.gz \
  https://cdn.zabbix.com/zabbix/sources/oldstable/5.0/zabbix-5.0.47.tar.gz
tar xzf z.tar.gz --wildcards "*/import/validators/C50XmlValidator.php"
```

Validátor pro verzi N je `C<N>XmlValidator.php` (`C50`, `C54`, `C60`…).
Je to jedno velké pole `'tag' => ['type' => ..., 'rules' => [...]]`, kde
**úroveň odsazení tabulátory = zanoření v XML**. Vytáhni povolené potomky:

```bash
python3 - <<'PY'
import re
L = open('C50XmlValidator.php').read().split('\n')
for j, line in enumerate(L):
    m = re.match(r"^(\t*)'(\w+)'\s*=>", line)
    if m and 1600 < j < 1660:          # rozsah bloku, ktery te zajima
        print(f"tabs={len(m.group(1))}  {m.group(2)}")
PY
```

Stejný tarball má v `database/mysql/data.sql` i **výchozí skupiny** dané
verze — hodí se, protože import skupiny nezakládá (viz §4).

## 3. Kostra pro Zabbix 5.0 (XML)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<zabbix_export>
    <version>5.0</version>
    <date>2026-01-01T00:00:00Z</date>
    <groups>
        <group><name>Templates</name></group>
    </groups>
    <templates>
        <template>
            <template>Můj Template</template>
            <name>Můj Template</name>
            <description>...</description>
            <groups><group><name>Templates</name></group></groups>
            <applications><application><name>Battery</name></application></applications>
            <items>
                <item>
                    <name>State of charge</name>
                    <type>SNMP_AGENT</type>
                    <snmp_oid>.1.3.6.1.4.1.99999.1.1.4.0</snmp_oid>
                    <key>bms.soc</key>
                    <delay>1m</delay>
                    <history>31d</history>
                    <trends>365d</trends>
                    <value_type>FLOAT</value_type>
                    <units>%</units>
                    <applications><application><name>Battery</name></application></applications>
                    <preprocessing>
                        <step><type>MULTIPLIER</type><params>0.001</params></step>
                    </preprocessing>
                </item>
            </items>
            <macros>
                <macro><macro>{$SNMP_COMMUNITY}</macro><value>public</value></macro>
            </macros>
        </template>
    </templates>
    <triggers>
        <trigger>
            <expression>{Můj Template:bms.soc.last()}&lt;20</expression>
            <name>Battery critically discharged</name>
            <priority>HIGH</priority>
        </trigger>
    </triggers>
    <graphs>
        <graph>
            <name>State of charge</name>
            <yaxismin>0</yaxismin><yaxismax>100</yaxismax>
            <ymin_type_1>FIXED</ymin_type_1><ymax_type_1>FIXED</ymax_type_1>
            <graph_items>
                <graph_item>
                    <sortorder>0</sortorder>
                    <drawtype>BOLD_LINE</drawtype>
                    <color>1A7C11</color>
                    <yaxisside>LEFT</yaxisside>
                    <calc_fnc>AVG</calc_fnc>
                    <item><host>Můj Template</host><key>bms.soc</key></item>
                </graph_item>
            </graph_items>
        </graph>
    </graphs>
</zabbix_export>
```

**Povolení potomci `<template>` v 5.0**, v tomhle pořadí:
`template, name, description, templates, groups, applications, items,
discovery_rules, httptests, tags, macros, screens`

**Pozor na `<item>` ve dvou významech:** v šabloně je to definice položky,
uvnitř `<graph_item>` jen odkaz `host` + `key`, kde `host` je **jméno
šablony**. Validátory postavené na ploché mapě `tag → potomci` na tomhle
padnou; pravidlo musí být vázané na rodiče.

XML escapuj `<`, `>` a `&` — výrazy triggerů jsou jich plné.

## 4. Chyby při importu a jejich příčiny

| Hláška | Příčina a řešení |
|---|---|
| `Unsupported import file extension "yaml"` | Zabbix < 5.2 YAML neumí. Použij XML nebo JSON. |
| `unexpected tag "triggers"` | V ≤ 5.2 patří `triggers`, `graphs` i `value_maps` na **kořen**, ne do šablony. |
| `Group "..." does not exist.` | **Import skupiny nezakládá.** Založ ji předem, nebo použij `Templates` (`groupid 1`, existuje vždy). Názvy se navíc liší: 5.0 má `Templates/Network devices`, 6.0 to přejmenovalo na `Templates/Net devices`. |
| `Cannot find value map "..." used for item "..."` | V 5.0 má `CConfigurationImport.php` value mapy natvrdo vypnuté (`createMissing => false`) a frontend pro ně **nemá zaškrtávátko**. Buď odkazy na mapy vynech (stavy se zobrazí čísly), nebo mapy založ ručně v *Administration → General → Value mapping*. Od 6.0 jsou součástí šablony a problém odpadá. |
| `Invalid tag ...: unexpected tag "uuid"` | UUID až od 6.0. Do staršího formátu nepatří. |
| `Incorrect trigger expression` | Verze ≤ 5.2 chce `{Tpl:key.last()}`, od 5.4 `last(/Tpl/key)`. |

## 5. Chyby na straně hosta

Tyhle přijdou **po** úspěšném importu, při připojení šablony k hostovi.

| Hláška | Příčina |
|---|---|
| `Cannot find host interface on "<host>" for item key "..."` | Host nemá interface odpovídající typu položek. SNMP položky vyžadují **SNMP interface**, a ten musí existovat **dřív**, než šablonu přilepíš. |
| položky *Not supported*, `Timeout` | Nesedí community (makro `{$SNMP_COMMUNITY}` na hostu vs. nastavení zařízení), nebo je zařízení nedosažitelné. Ověř `snmpget -v2c -c <community> <ip> .1.3.6.1.2.1.1.5.0`. |
| `Received empty response` u GETBULK | Agent nezvládne tolik varbindů. Sniž *Max repetition count* na SNMP interface. |

**Pořadí při zakládání hosta:** interface → makra → teprve pak šablona.

## 6. Generátor místo ručního psaní

Když šablona pokrývá vlastní MIB, udržuj **jednu tabulku OID** a z ní generuj
všechny formáty. Ruční údržba dvou souborů se rozejde a nikdo si toho nevšimne,
dokud trigger nepřestane sepínat.

```python
ITEMS = [
    # name, key, oid, value_type, units, multiplier, valuemap, application
    ("State of charge", "bms.soc", ".1.1.4.0", "FLOAT", "%", None, None, "Battery"),
]
TRIGGERS = [
    # nazev, vyraz pro 6.0+, vyraz pro 5.0, priorita, popis
    ("Battery critically discharged",
     "last(/{T}/bms.soc)<{$SOC.CRIT}",
     "{{T}:bms.soc.last()}<{$SOC.CRIT}",
     "HIGH", "..."),
]
```

Výrazy triggerů piš pro obě syntaxe **ručně**. Automatický převod
`last(/T/k)` ↔ `{T:k.last()}` vypadá mechanicky, ale rozbije se na funkcích
s parametry (`min(/T/k,30m)` → `{T:k.min(30m)}`), na složených výrazech
a na makrech.

**UUID pro 6.0+** odvozuj deterministicky z klíče položky (např. prvních
32 znaků SHA-1). Náhodná UUID při každém generování způsobí, že re-import
založí duplicitní objekty místo aktualizace existujících.

## 7. Validace před importem

V repu skillu je `scripts/check_zabbix_xml.py` — projde celý soubor a vypíše
**všechny** problémy najednou, ne jen první. Kontroluje:

- povolené tagy podle schématu 5.0 (včetně rozlišení `<item>` podle rodiče),
- `triggers` / `graphs` / `value_maps` omylem vnořené do šablony,
- skupinu, která ve výchozí instalaci neexistuje,
- odkazy na neexistující aplikace, value mapy a položky (i z grafů),
- zdvojené složené závorky ve výrazech (klasická chyba při skládání řetězců),
- novou syntaxi triggerů v souboru pro starou verzi.

```bash
python3 scripts/check_zabbix_xml.py muj-template-5.0.xml
```

Pusť ho po každém generování. Když si ho rozšíříš o novou třídu chyby, kterou
jsi právě schytal, příště už tě nepřekvapí.

## 8. Ověření po nasazení

```bash
snmpget     -v2c -c <community> <ip> .1.3.6.1.2.1.1.5.0       # sysName
snmpwalk    -v2c -c <community> <ip> .1.3.6.1.4.1.<pen>       # GETNEXT
snmpbulkwalk -v2c -c <community> <ip> .1.3.6.1.4.1.<pen>      # GETBULK
```

Pokud `snmpwalk` projde a `snmpbulkwalk` skončí `tooBig`, agent nezvládá
tolik varbindů na odpověď. Najdi strop pokusem (`-Cr10`, `-Cr14`, `-Cr20`)
a nastav *Max repetition count* na interface pod něj.

V Zabbixu pak *Monitoring → Latest data*. **Grafy se objeví až po prvním
sběru dat**, ne hned po importu.

## 9. Enterprise OID

Vlastní větev `.1.3.6.1.4.1.<PEN>` vyžaduje číslo přidělené IANA — je
**zdarma** na <https://www.iana.org/assignments/enterprise-numbers/>.
Do doby, než ho firma má, drž placeholder v jediné konstantě a nikdy ho
nepouštěj mimo vlastní síť.
