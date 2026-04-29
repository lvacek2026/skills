# net-config-backups

Automatizované zálohy konfigurací síťových zařízení.

> ⚠️ **Tento repo zapisuje výhradně Oxidized robot.** Lidský commit do tohoto repa je policy violation.
> Změny v IaC (Oxidized config, router.db, n8n workflows) řešte v repu [`net-infra-iac`](https://github.com/org/net-infra-iac).

## Co tady najdete

```
/sites/
  /praha/
    SW_Kotelna_hlavni        ← display current-configuration all
    SW_Kotelna_FTTB
    Huawei6730_tyrsova
  /brno/
    ...
```

Každý soubor je jeden snapshot konfigurace zařízení v plain textu, aktualizovaný Oxidized daemonem.

## Jak najít konkrétní změnu

```bash
# Co se změnilo na Tyršově za poslední týden
git log --since="1 week ago" -- sites/praha/Huawei6730_tyrsova

# Diff mezi dvěma snapshoty
git show <hash>:sites/praha/Huawei6730_tyrsova
git diff <hash1> <hash2> -- sites/praha/Huawei6730_tyrsova

# Kdo (které zařízení) se měnilo nejčastěji
git log --pretty=format: --name-only | sort | uniq -c | sort -rn | head -20
```

## Restore workflow při havárii

Viz [skill `network-config-backup-repo`](https://github.com/org/net-infra-iac/tree/main/skills/network-config-backup-repo) sekce *Disaster recovery*.

## Bezpečnost

- Repo je **private**, GitHub Push Protection enabled
- Push protection blokuje secret leaks (API tokens, AWS keys)
- Branch protection: `main` může pushovat pouze deploy key `oxidized-bot`
- Konfigurace obsahují hash hesel a SNMP communities — **nikdy nesdílet snapshots mimo organizaci**

## Cadence

- Plánovaný snapshot: denně 06:00 UTC (cron v Oxidized)
- Manuální trigger: n8n workflow `network-backup-on-demand` (Slack `/backup <device>`)
- Po-change snapshot: TODO — webhook ze syslog serveru při detekci `CONFIGCHANGED`
