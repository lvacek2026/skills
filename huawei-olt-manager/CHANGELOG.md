# Changelog

Všechny významné změny tohoto skillu se zaznamenávají do tohoto souboru.

Formát vychází z [Keep a Changelog](https://keepachangelog.com/cs/1.1.0/)
a verzování dle [SemVer](https://semver.org/lang/cs/).

## [0.2.0] – 2026-04-29

### Added
- Sekce 6 "Onboarding nového uživatele a SSH RSA klíče" — kompletní postup
  pro MA5603T V800R018C10:
  - Krok 6.1: import RSA peer-public-key (PKCS#1 hex, 2048-bit max, wrap 64)
  - Krok 6.2: interaktivní wizard `terminal user name` s kompletním seznamem
    všech promptů (Username, Password, Confirm, Profile, Level, Permitted
    Reenter Number, Appended Info)
  - Krok 6.3: mapping SSH user → RSA klíč přes `ssh user X authentication-type`
    + `ssh user X assign rsa-key NAME`. Auth-type možnosti: rsa, password,
    password-publickey, all
  - Krok 6.4: persistence přes `save`
- Známý problém: Oxidized 0.36 (Ruby net-ssh) → MA5603T R018 padding error.
  Důkaz že problém je na klientské straně (openssh funguje), navržené workaroundy.
- Diagnostika "Connection reset by peer" — kde hledat refuse ACL, IP-access,
  firewall, session count, anti-bruteforce cooldown.
- Konverze OpenSSH klíče na PKCS#1 hex pro MA56xx (ssh-keygen + openssl).

### Notes
- Postup ověřen: 2026-04-29 onboarding Gpon_Bezdekov (MA5603T V800R018C10)
  pro `ia_asistent` (diagnostika) a `n8n_backup` (Oxidized).
- Pravidla pro klíč (PKCS#1, 2048-bit, wrap 64) pochází z dřívějšího
  výzkumu na S6730 V200R019C00 (memory `project_huawei_vrp_keys`).

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
