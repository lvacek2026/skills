#!/usr/bin/env python3
"""Overi vygenerovanou Zabbix 5.0 XML sablonu proti skutecnemu schematu.

Povolene prvky jsou vytazene z
    ui/include/classes/import/validators/C50XmlValidator.php
ze zdrojaku Zabbixu 5.0.47 (cdn.zabbix.com/zabbix/sources/oldstable/5.0/).

Duvod, proc tohle existuje: import v Zabbixu hlasi vzdycky jen PRVNI spatny
tag, takze oprava naslepo znamena kolo pokus-omyl za kazdou chybu. Tenhle
skript najde vsechny naraz a hlavne pripomene, ze v 5.0 jsou <triggers>,
<graphs> i <value_maps> KORENOVE prvky — az 5.4 je presunula do sablony.

    python3 tools/check_zabbix_xml.py zabbix/viridium-battery-snmp-5.0.xml
"""
import sys
import xml.etree.ElementTree as ET

# Element -> mnozina povolenych primych potomku (Zabbix 5.0.47).
SCHEMA = {
    "zabbix_export": {"version", "date", "groups", "hosts", "templates",
                      "triggers", "graphs", "value_maps", "media_types",
                      "maps", "images", "screens"},
    "groups":        {"group"},
    "group":         {"name", "uuid"},
    "templates":     {"template"},
    "template":      {"template", "name", "description", "templates", "groups",
                      "applications", "items", "discovery_rules", "httptests",
                      "tags", "macros", "screens"},
    "applications":  {"application"},
    "application":   {"name"},
    "items":         {"item"},
    "item":          {"name", "type", "snmp_oid", "key", "delay", "history",
                      "trends", "status", "value_type", "allowed_hosts", "units",
                      "params", "ipmi_sensor", "authtype", "username", "password",
                      "publickey", "privatekey", "description", "inventory_link",
                      "applications", "valuemap", "logtimefmt", "preprocessing",
                      "jmx_endpoint", "master_item", "timeout", "url",
                      "query_fields", "posts", "status_codes", "follow_redirects",
                      "post_type", "http_proxy", "headers", "retrieve_mode",
                      "request_method", "output_format", "ssl_cert_file",
                      "ssl_key_file", "ssl_key_password", "verify_peer",
                      "verify_host", "triggers", "tags"},
    "valuemap":      {"name"},
    "preprocessing": {"step"},
    "step":          {"type", "params", "error_handler", "error_handler_params"},
    "macros":        {"macro"},
    "macro":         {"macro", "value", "type", "description"},
    "triggers":      {"trigger"},
    "trigger":       {"expression", "recovery_mode", "recovery_expression",
                      "correlation_mode", "correlation_tag", "name", "opdata",
                      "url", "status", "priority", "description", "type",
                      "manual_close", "dependencies", "tags"},
    "graphs":        {"graph"},
    "graph":         {"name", "width", "height", "yaxismin", "yaxismax",
                      "show_work_period", "show_triggers", "type", "show_legend",
                      "show_3d", "percent_left", "percent_right", "ymin_type_1",
                      "ymin_item_1", "ymax_type_1", "ymax_item_1", "graph_items"},
    "graph_items":   {"graph_item"},
    "graph_item":    {"sortorder", "drawtype", "color", "yaxisside", "calc_fnc",
                      "type", "item"},
    # <item> ma jiny vyznam v grafu (odkaz host+key) nez v sablone (definice
    # polozky), takze se rozlisuje podle rodice.
    "graph_item/item": {"host", "key"},
    "value_maps":    {"value_map"},
    "value_map":     {"name", "mappings"},
    "mappings":      {"mapping"},
    "mapping":       {"value", "newvalue"},
}

# Prvky, ktere v 5.0 NESMI byt uvnitr sablony (presunuly se tam az v 5.4).
ROOT_ONLY = {"triggers", "graphs", "value_maps"}

# Vychozi skupiny ciste instalace Zabbixu 5.0 (database/mysql/data.sql).
# Import skupiny NEZAKLADA, takze odkaz na neexistujici skupinu shodi cely
# import hlaskou 'Group "..." does not exist.'. Pozor na prejmenovani:
# 6.0 ma "Templates/Net devices", pětka "Templates/Network devices".
DEFAULT_GROUPS_50 = {
    "Templates", "Templates/Applications", "Templates/Databases",
    "Templates/Modules", "Templates/Network devices",
    "Templates/Operating systems", "Templates/Power", "Templates/SAN",
    "Templates/Server hardware", "Templates/Telephony",
    "Templates/Virtualization",
}


def walk(el, path, problems, parent=None):
    # Nejdriv zkus pravidlo vazane na rodice, pak obecne podle nazvu tagu.
    allowed = SCHEMA.get(f"{parent}/{el.tag}") if parent else None
    if allowed is None:
        allowed = SCHEMA.get(el.tag)
    if allowed is None:
        return                      # listovy prvek, obsah neresime
    for child in el:
        p = f"{path}/{child.tag}"
        if child.tag not in allowed:
            hint = ""
            if child.tag in ROOT_ONLY:
                hint = (f"  <- v Zabbixu 5.0 patri <{child.tag}> na KOREN, "
                        "ne do sablony")
            problems.append(f"nepovoleny tag {p}{hint}")
        walk(child, p, problems, el.tag)


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "zabbix/viridium-battery-snmp-5.0.xml"
    root = ET.parse(path).getroot()

    problems = []
    warnings = []
    if root.tag != "zabbix_export":
        problems.append(f"korenovy prvek je <{root.tag}>, ceka se <zabbix_export>")
    walk(root, "/" + root.tag, problems)

    for g in root.findall("groups/group"):
        name = g.findtext("name")
        if name not in DEFAULT_GROUPS_50:
            problems.append(
                f"skupina {name!r} neni mezi vychozimi skupinami Zabbixu 5.0 — "
                "import ji NEZALOZI a skonci chybou. Bud ji na serveru vytvor "
                "rucne, nebo pouzij nazev z DEFAULT_GROUPS_50.")

    version = root.findtext("version")
    if version != "5.0":
        problems.append(f"<version> je {version!r}, ceka se '5.0'")
    if root.find("date") is None:
        problems.append("chybi povinny <date>")

    # Krizove kontroly, ktere schema neresi, ale import ano
    tpl = root.find("templates/template")
    if tpl is not None:
        keys = {i.findtext("key") for i in tpl.findall("items/item")}
        apps = {a.findtext("name") for a in tpl.findall("applications/application")}
        for i in tpl.findall("items/item"):
            for a in i.findall("applications/application"):
                if a.findtext("name") not in apps:
                    problems.append(f"polozka {i.findtext('key')} odkazuje na "
                                    f"nedeklarovanou aplikaci {a.findtext('name')!r}")
        # Zabbix 5.0 value mapy pri importu NEVYTVARI (CConfigurationImport:84,
        # frontend pro ne nema zaskrtavatko) a odkaz na neexistujici mapu shodi
        # cely import. Soubor s odkazy jde pouzit, az kdyz uz mapy na serveru
        # rucne existuji — proto jen upozorneni, ne chyba.
        refs = [i for i in tpl.findall("items/item") if i.find("valuemap") is not None]
        if refs:
            vms = {v.findtext("name") for v in root.findall("value_maps/value_map")}
            for i in refs:
                vm = i.findtext("valuemap/name")
                if vm and vm not in vms:
                    problems.append(f"polozka {i.findtext('key')} odkazuje na "
                                    f"value map {vm!r}, ktera v souboru neni")
            warnings.append(
                f"{len(refs)} polozek odkazuje na value mapy. Zabbix 5.0 je pri "
                "importu NEVYTVORI — nejdriv je zaloz rucne v Administration -> "
                "General -> Value mapping, jinak import skonci chybou "
                "'Cannot find value map'.")
        # Grafy odkazuji polozky dvojici host+key, kde "host" je jmeno sablony.
        tpl_name = tpl.findtext("template")
        for g in root.findall("graphs/graph"):
            for gi in g.findall("graph_items/graph_item"):
                h, k = gi.findtext("item/host"), gi.findtext("item/key")
                if h != tpl_name:
                    problems.append(f"graf {g.findtext('name')!r} odkazuje na "
                                    f"hosta {h!r}, ceka se {tpl_name!r}")
                if k not in keys:
                    problems.append(f"graf {g.findtext('name')!r} odkazuje na "
                                    f"neexistujici polozku {k!r}")

        for t in root.findall("triggers/trigger"):
            e = t.findtext("expression") or ""
            if "{{" in e or "}}" in e:
                problems.append(f"trigger {t.findtext('name')!r} ma zdvojene zavorky")
            if "last(/" in e or "min(/" in e or "max(/" in e:
                problems.append(f"trigger {t.findtext('name')!r} pouziva NOVOU "
                                "syntaxi (5.4+), 5.0 chce {Template:key.last()}")

    if warnings:
        print("UPOZORNENI:")
        for w in warnings:
            print("  !", w)
        print()

    if problems:
        print(f"NALEZENO {len(problems)} problemu:")
        for p in problems:
            print("  -", p)
        return 1

    tpl_name = root.findtext("templates/template/template")
    print(f"OK  {path}")
    print(f"    sablona   : {tpl_name}")
    print(f"    polozek   : {len(root.findall('templates/template/items/item'))}")
    print(f"    triggeru  : {len(root.findall('triggers/trigger'))}")
    print(f"    grafu     : {len(root.findall('graphs/graph'))}")
    print(f"    value map : {len(root.findall('value_maps/value_map'))}")
    print(f"    maker     : {len(root.findall('templates/template/macros/macro'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
