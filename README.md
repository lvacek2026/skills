# Skills for Claude Code

Kolekce skillů pro Claude Code (AI coding assistant od Anthropic).

## Instalace
```bash
npx skills add https://github.com/lvacek2026/skills --skill <název-skillu> -g
```

Parametr `-g` nainstaluje skill globálně (dostupný ve všech projektech).

## Dostupné skilly

### 🪟 liquid-glass
Expert na Apple Liquid Glass UI/UX design a SwiftUI implementaci.
```bash
npx skills add https://github.com/lvacek2026/skills --skill liquid-glass -g
```

**Obsahuje:**
- Architektonická pravidla a vrstvení
- Typografie a barevná paleta
- Interaktivní stavy (Focus, Pressed, Disabled)
- Přístupnost a fallback design
- SwiftUI syntaxe a implementace

## Struktura repozitáře
```
skills/
└── liquid-glass/
    └── SKILL.md
```

## Přidání nového skillu

Každý skill musí obsahovat `SKILL.md` s YAML frontmatterem:
```yaml
---
name: název-skillu
description: "Popis kdy a jak Claude skill použije."
---

# Obsah skillu...
```
