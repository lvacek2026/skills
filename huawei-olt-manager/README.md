# huawei-olt-manager

Claude Code / Cowork skill pro automatizaci jednotek **Huawei SmartAX MA5683T OLT**
(firmware **V800R015C00**) přes SSH.

Skill řeší specifika R015: nestabilní `screen-length`, asynchronní alarmy,
povinná interaktivní potvrzení a deterministický workflow pro provisioning ONT,
diagnostiku optiky (DDM) a kontrolu hardwaru.

## Obsah

- `SKILL.md` – samotný skill (frontmatter + playbook).

## Instalace

### Claude Code (lokální skills)

```bash
# Z kořene tohoto repa zkopíruj složku skillu do uživatelských skills.
mkdir -p ~/.claude/skills
cp -r huawei-olt-manager ~/.claude/skills/
```

Po restartu Claude Code se skill automaticky nabídne při relevantních dotazech
(viz `description` ve frontmatteru).

### Claude Code plugin (sdílený)

Pokud distribuuješ sadu skillů jako plugin, vlož složku `huawei-olt-manager/`
do `skills/` adresáře pluginu a publikuj přes plugin marketplace.

## Použití

Skill se spustí automaticky, pokud uživatel zmíní např.:

- "potřebuju zautorizovat novou ONT na MA5683T"
- "zkontroluj DDM na portu 0/3/12"
- "co znamená `Failed` u `display board 0`"
- "nakonfiguruj service-port pro VLAN 100 na GPON"

Manuálně lze invokovat přes `/skills huawei-olt-manager` (Claude Code).

## Verzování

- **0.1.0** – první veřejná verze: SSH session prep, provisioning workflow,
  DDM diagnostika, antipatterns.

## Licence

MIT (viz `LICENSE`).
