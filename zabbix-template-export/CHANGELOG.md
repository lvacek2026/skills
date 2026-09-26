# Changelog

## [1.0.0] — 2026-09-26

První verze. Vznikla z reálného nasazení SNMP šablony na Zabbix 5.0.47, kde
se postupně objevilo šest různých důvodů, proč import selže — a každý z nich
Zabbix ohlásil až poté, co byl opravený ten předchozí.

### Obsahuje

- Tabulku rozdílů formátu mezi Zabbix 5.0 / 5.2 / 5.4 / 6.0+
- Postup, jak si stáhnout autoritativní schéma ze zdrojáků dané verze
  (`C<N>XmlValidator.php` z tarballu na cdn.zabbix.com, pozor na `oldstable`)
- Kompletní kostru šablony pro 5.0 včetně triggerů a grafů
- Tabulku chybových hlášek a jejich příčin — pro import i pro připojení
  šablony k hostovi
- Doporučený tvar generátoru (jedna tabulka OID → všechny formáty)
- Validátor `scripts/check_zabbix_xml.py`
