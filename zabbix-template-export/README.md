# zabbix-template-export

Claude Code skill pro **tvorbu a import Zabbix šablon** napříč verzemi 5.0 až 7.x.

Import v Zabbixu hlásí vždycky jen **první** špatný tag, takže oprava naslepo
znamená kolo pokus-omyl za každou chybu. Skill shrnuje rozdíly formátu mezi
verzemi, postup jak si stáhnout autoritativní schéma přímo ze zdrojáků,
a validátor, který soubor zkontroluje celý najednou.

## Co skill řeší

- **Rozdíly formátu** — YAML až od 5.2, UUID od 6.0, `applications` vs tagy,
  stará vs nová syntaxe triggerů, kořenové vs vnořené `triggers` / `graphs` /
  `value_maps`
- **Tabulku chyb → příčin** pro import i pro připojení šablony k hostovi
- **Získání schématu ze zdrojáků** (`C50XmlValidator.php` z tarballu na CDN)
- **Generátor** — jedna tabulka OID, z ní všechny formáty
- **Validaci před importem** — `scripts/check_zabbix_xml.py`

## Obsah

- `SKILL.md` – samotný skill
- `scripts/check_zabbix_xml.py` – validátor XML proti schématu Zabbix 5.0

## Instalace

```bash
npx skills add https://github.com/lvacek2026/skills --skill zabbix-template-export -g
```

Nebo ručně:

```bash
mkdir -p ~/.claude/skills
cp -r zabbix-template-export ~/.claude/skills/
```

## Použití validátoru

```bash
python3 ~/.claude/skills/zabbix-template-export/scripts/check_zabbix_xml.py muj-template-5.0.xml
```

Vypíše **všechny** problémy najednou a u typických chyb i vysvětlení
(např. že `<triggers>` patří v 5.0 na kořen, ne do šablony).
