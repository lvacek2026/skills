# Changelog

Všechny významné změny tohoto skillu se zaznamenávají do tohoto souboru.

Formát vychází z [Keep a Changelog](https://keepachangelog.com/cs/1.1.0/)
a verzování dle [SemVer](https://semver.org/lang/cs/).

## [0.1.0] – 2026-04-28

### Added
- První veřejná verze skillu `huawei-olt-manager`.
- Sekce 1: příprava SSH relace (`scroll 512`, `undo smart`, `undo alarm output all`).
- Sekce 2: zpracování interaktivních Y/N dotazů s bezpečnostní pojistkou
  pro `delete/clear/reset/reboot`.
- Sekce 3: provisioning workflow (autofind → autorizace → service-port).
- Sekce 4: diagnostika optiky (DDM) a stavu hardwaru.
- Sekce 5: ukládání konfigurace.
- Sekce 6: technické limity (Privilege Level 3, 22 SSH, 60s auth timeout).
- Sekce 7: doporučený výstupní formát.
- Sekce 8: antipatterns.
