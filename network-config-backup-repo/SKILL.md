---
name: network-config-backup-repo
description: Use when designing, creating, or migrating a Git repository for automated network device configuration backups (Oxidized, RANCID, NAPALM). Covers split-repo vs monorepo decisions, branch strategy, directory layout, Oxidized integration, security hardening (secret scanning, branch protection), and a migration playbook for repos with divergent main/master branches that never meet.
---

# Network Config Backup Repo

Profesionální architektura Git repozitáře pro automatizované zálohy konfigurací síťových zařízení (Huawei VRP, Cisco IOS, MikroTik, atd.) zálohovaných nástrojem Oxidized + n8n + GitHub.

## Kdy tento skill použít

- Navrhuje se nové repo pro síťové backupy
- Existující repo má divergované větve (např. `main` pro IaC + `master` pro Oxidized push, které se nikdy nesetkají)
- Roste počet zařízení (5 → 50 → 500) a flat struktura přestává stačit
- Hledá se profesionální setup, který přežije růst infrastruktury

## Architektura: Split-repo (doporučeno)

Průmyslovým standardem pro NetDevOps je **oddělení IaC kódu (logika) od config snapshotů (data)**:

| Repo                  | Obsah                                              | Kdo zapisuje                  | Cadence změn         |
| --------------------- | -------------------------------------------------- | ----------------------------- | -------------------- |
| `net-infra-iac`       | Docker compose, n8n workflows, Oxidized config, docs, switch-prep skripty | Lidé přes Pull Requesty       | Týdně až měsíčně     |
| `net-config-backups`  | Čisté zálohy konfigurací zařízení (raw text)       | Výhradně Oxidized robot       | Denně až po každé změně |

**Hlavní výhoda:** desítky automatických commitů denně nezahltí historii vašeho IaC kódu a neznefunkční nástroj `git blame`. Audit kódu a audit konfigurací mají různé recenzenty a různý workflow.

## Migrační playbook (z divergentního stavu)

Pokud máte aktuálně IaC na `main` a zálohy na `master` ve stejném repu:

### Krok 1: Vytvořit nové prázdné repo na GitHubu

```bash
gh repo create org/net-config-backups --private --description "Automated network device config backups (Oxidized)"
```

### Krok 2: Izolovat zálohy do nového repa

```bash
git clone --branch master <PUVODNI_REPO> backup-migration
cd backup-migration

# Smaž IaC soubory ze záloh
git rm -rf infrastructure/ docker-compose.yml README.md docs/
git commit -m "chore: isolate backup history from IaC"

# Přepoj na nové repo a pushni master historii jako main
git remote set-url origin <URL_NEW_BACKUP_REPO>
git push origin master:main
```

### Krok 3: Vyčistit IaC repo

V původním repu smažte větev `master` (lokálně i na remote):

```bash
git push origin --delete master   # pozor: destruktivní, jen po ověření že nové repo má kompletní historii
git branch -D master
```

### Krok 4: Překonfigurovat Oxidized

V `oxidized/config` upravit `hooks.github_push.remote_repo` na URL nového backup repa. Restartovat Oxidized container.

### Krok 5: Aktualizovat README a docs v IaC repu

Doplnit odkaz na backup repo a vysvětlit dělbu rolí pro budoucí kolegy.

## Rozhodovací matice — adresářová struktura záloh

| Velikost sítě  | Doporučení                              | Argumentace                                          |
| -------------- | --------------------------------------- | ---------------------------------------------------- |
| 5–15 zařízení  | Flat (`/<hostname>`)                    | Jednoduchost, Oxidized default, rychlý přehled.      |
| 15–50 zařízení | Hierarchie dle lokalit (`/sites/<site>/<hostname>`) | Škálovatelnost, přehlednost pro inženýry.   |
| 50+ zařízení   | Hierarchie Site/Vendor/Role (`/sites/<site>/<vendor>/<role>/<hostname>`) | Nutnost pro automatizaci přes n8n, granulární CODEOWNERS. |

V Oxidized configu se hierarchie zapne přes `output.git.subdirectories: true` a definicí `groups` v `router.db`.

## Anti-patterny (čemu se vyhnout)

### ❌ Divergované větve v monorepu

Stav, kdy `main` (IaC) a `master` (zálohy) ve stejném repu nikdy nesetkají. **Nejčastější začátečnická chyba.** Důsledky:
- Backup soubory jsou pro běžného návštěvníka GitHubu neviditelné (default branch je `main`)
- `git log`, `git blame`, GitHub Insights ukazují zkreslený obraz
- Nedá se nasadit smysluplný branch protection — každá branch má jiný workflow

**Řešení:** split-repo migrací viz playbook výše.

### ❌ Zasílání timestampů z VRP

Huawei VRP vkládá aktuální čas do výstupu `display current-configuration`. Bez sanitizace bude Oxidized commitovat každou hodinu, i když se nic věcně nezměnilo.

**Řešení:** v Oxidized modelu pro `vrp` filtrovat řádky s timestampem (regex), nebo na zařízení vypnout vkládání času (`undo info-center timestamp`).

### ❌ Privátní klíče v Gitu

Nikdy neukládat SSH klíče do IaC repa, ani jako "test" nebo "example".

**Řešení:** klíče v Docker volumes nebo GitHub Secrets / Environment variables. V `.gitignore` blokovat `id_*`, `*.pem`, `*.key`.

### ❌ Public repo bez secret scanningu

Konfigurace zařízení obsahují hash hesel, SNMP communities, RADIUS shared keys. Při omylem public push je to instantní kompromitace.

**Řešení:** repo **vždy private** + GitHub Push Protection + pre-receive hook na sanitaci (např. odfiltrovat `snmp-agent community`).

## Šablony

V adresáři `templates/` jsou připravené šablony:

- `oxidized_config.yaml` — kompletní Oxidized config pro split-repo + githubrepo hook
- `gitignore` — pro IaC i backup repo (runtime files, n8n data, Caddy certs)
- `CODEOWNERS` — granulární kontrola dle lokalit
- `README.md` — šablona pro backup repo

## Branch protection (GitHub)

Pro `net-config-backups`, branch `main`:

| Setting                     | Hodnota                                            | Důvod                                                 |
| --------------------------- | -------------------------------------------------- | ----------------------------------------------------- |
| Restrict pushes             | Pouze deploy key Oxidized daemonu                  | Žádný člověk nesmí přepsat historii záloh.            |
| Require signed commits      | Doporučeno                                         | Auditovatelnost — kdo/kdy zálohu vytvořil.            |
| Require linear history      | Vypnout                                            | Oxidized fast-forward push by se neprovedl.           |
| Allow force push            | **Disable**                                        | Historie záloh musí být immutable.                    |
| Allow deletions             | **Disable**                                        | Ochrana před omylem.                                  |

Pro `net-infra-iac`, branch `main`:

| Setting                     | Hodnota                                            |
| --------------------------- | -------------------------------------------------- |
| Require pull request review | Min. 1 reviewer                                    |
| Dismiss stale reviews       | Enable                                             |
| Require status checks       | Lint, secret scan, docker build                    |
| Require signed commits      | Doporučeno                                         |
| CODEOWNERS enforcement      | Enable                                             |

## Commit hygiene

Oxidized default commit message: `update /<device>`. Pro malé/střední sítě dostatečné.

Pro 50+ zařízení doporučeno přepsat na strukturovaný formát přes Oxidized `model` hook:
```
update <site>/<hostname> [vrp 5.170]

Diff: 12 lines changed
Triggered by: scheduled (06:00 UTC)
```

**Squashovat NE** — každý snapshot v čase je hodnota. Místo squashe periodicky archivovat (viz Retence).

## Retence a velikost repa

Při 500 zařízení × denní snapshot × 5 let ≈ 900k commitů, repo desítky GB.

Strategie pro produkci:
- **Ročně** vytvořit archivní repo `net-config-backups-YYYY` a "rotate" aktivní repo (smazat starší než 13 měsíců)
- **Shallow clones** pro CI (`git clone --depth 30`)
- **Git LFS** pouze pro velké binary configy (Cisco show-tech archivy) — pro plain text VRP/IOS configy zbytečné
- **`.gitattributes`** s `*.cfg diff=cfg` a vlastním textconv pro hezké diffy

## Disaster recovery — restore workflow

Při havárii zařízení:

```bash
# Najdi poslední validní snapshot před incidentem
git log --oneline --before="2026-04-27 14:00" -- sites/praha/SW_kotelna_hlavni

# Vytisknì obsah
git show <hash>:sites/praha/SW_kotelna_hlavni > restore.cfg

# Diff proti aktuálnímu stavu
git diff <hash> HEAD -- sites/praha/SW_kotelna_hlavni
```

Skutečné nahrání zpět do zařízení je out-of-scope tohoto skillu (TFTP/SCP push závislý na vendoru).

## Reference

- Oxidized README — https://github.com/ytti/oxidized
- Oxidized hooks dokumentace — `docs/Hooks.md` v Oxidized repu
- RANCID best practices — http://www.shrubbery.net/rancid/
- NetDevOps Slack #netdevops, #oxidized kanály
- NetBox / Nautobot komunitní vzory — https://github.com/netbox-community
