# cz-telco-regulace

Claude Code skill — expert na českou regulaci telekomunikačních služeb
z pohledu poskytovatele internetu (ISP).

## K čemu to je

Skill dává Claudovi přesná fakta o:

- smluvních závazcích a předčasném ukončení smlouvy (prahy 3 měsíce, 5 %,
  24 měsíců);
- sankcích za odchod od operátora a výjimkách (zařízení na splátky);
- přenosu služby přes OKU kód — proces, lhůty, povinnosti opouštěného
  a přejímajícího poskytovatele;
- přenosu telefonního čísla;
- právech spotřebitele při změně operátora.

Hodí se při přípravě marketingových materiálů ISP (letáky, akce na akvizici
zákazníků od konkurence), argumentačních a školicích podkladů pro techniky
a obchodníky, smluvních podmínek, nebo chatbotů, které mají odpovídat
zákazníkům na otázky o přechodu a závazcích.

Cílem je, aby tvrzení o závazcích a přechodu byla právně přesná — klíčové
prahy se snadno pletou a chyba v letáku nebo na kartě technika je problém.

## Instalace

```bash
npx skills add https://github.com/lvacek2026/skills --skill cz-telco-regulace -g
```

## Struktura

```
cz-telco-regulace/
├── SKILL.md                          přehled + kdy skill použít
└── references/
    ├── zavazky-a-ukonceni.md         závazky, sankce, zařízení na splátky
    └── prenos-oku.md                 OKU proces, přenos čísla, lhůty
```

## Upozornění

Skill je marketingová a školicí pomůcka, ne právní poradenství. Vychází z webu
ČTÚ a zákona č. 127/2005 Sb. o elektronických komunikacích, stav ověřen k roku
2026. Regulace se vyvíjí — u kritických právních dokumentů ověřuj aktuálnost
přímo u zdroje (ctu.gov.cz) nebo konzultuj s právníkem se specializací na
telekomunikační právo.
