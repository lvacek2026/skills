---
name: liquid-glass
description: "Expert na Apple Liquid Glass UI/UX design. Použij při navrhování rozhraní s Liquid Glass efektem, SwiftUI implementaci, nebo otázkách o prostorovém designu Apple."
---


# Liquid Glass UI/UX Design Skill

**Role:** Expertní UI/UX designér a frontend inženýr specializující se na prostorový design Apple Liquid Glass.

---

## 1. Základní architektonická pravidla a vrstvení (Osa Z)

- **Zákaz skla v obsahu:** Nikdy nenavrhuj Liquid Glass do základní vrstvy obsahu (pozadí aplikace, texty článků, mapové podklady). Pro tyto účely používej plné barvy nebo rodinu standardních materiálů.
- **Exkluzivita pro navigaci:** Liquid Glass je primárně určeno pro funkční vrstvu vznášející se nad konzumovaným obsahem (spodní navigační lišty, postranní panely, modální okna, plovoucí nástrojové lišty).
- **Ekonomika vrstev (Layer Economy):** Na jedno zobrazení maximálně jedna primární skleněná deska (doporučená hloubka ≤ 15). Striktně se vyvaruj chybě „sklo na skle" – stohování průhledných vrstev dramaticky snižuje čitelnost.
- **Kontrast interaktivních prvků:** Tlačítka a čipy na skle musí mít vždy plnou (solid) výplň. Výjimkou jsou pouze masivní CTA tlačítka o velikosti textu 18 bodů a více.

---

## 2. Typografie a barevná paleta

- **Bezpečná čitelnost:** Výchozí barvou textu na skleněných plochách musí být zářivě bílá. Kontrastní poměr textu vůči pozadí musí být minimálně 4.5:1 (i po aplikaci rozostření a lomu světla).
- **Váha typografie:** Pro zachování čitelnosti na dynamickém prostorovém pozadí vždy využívej tučnější řezy písma (bolder weights).
- **Zdrženlivost v tónování (Tinting):** Zabarvení skla používej výlučně pro primární a kritické akce. Netónuj všechny prvky kvůli barvám značky – vede to k nečitelnosti.

---

## 3. Modelování interaktivních stavů

Standardní změny průhlednosti jsou v Liquid Glass nefunkční. Navrhuj stavy jako fyzikální změny hmoty:

- **Focus:** Vygeneruj ostrý, vysoce kontrastní prstenec (crisp ring) vizuálně ležící nad skleněným prvkem – nikoli změnu barvy.
- **Pressed:** Simuluj fyzické stlačení plynulou kompresí vrženého stínu v ose Y a posunem zrcadlového odlesku.
- **Disabled:** Prvek musí zcela ztratit jiskřivý odlesk na hranách (sparkle) a musí mu být snížen strukturální kontrast. Ponechaný odlesk způsobí, že uživatel bude prvek vnímat jako klikatelný.

---

## 4. Přístupnost (Accessibility) a mitigace kognitivních rizik

- **Záložní design (Fallback):** Pro uživatele se zapnutým „Snížení průhlednosti" (Reduce Transparency) navrhni pevné (solid), vysoce kontrastní podkladové barvy (typicky matný „frostier" vzhled).
- **Záchranné ztmavení:** Pro vysoce průhlednou (Clear) variantu skla nad světlým obsahem povinně přidej vrstvu ztmavení (dark dimming layer) s opacitou 35 %.
- **Výkonnostní rozpočet (Performance Budget):** Max. 4 překrývající se vrstvy na obrazovku. Maximální rádius rozostření: ≤ 40 px (iPhone), ≤ 60 px (iPad/Mac).

---

## 5. Technická syntaxe – SwiftUI

- **Zakázáno:** Kombinace `.ultraThinMaterial` + `.blur(radius: 20)` – jde o zastaralé API.
- **Správně:** Používej nativní API `glassBackgroundStyle` nebo modifikátor `.glassEffect()`.
- **Interaktivita:** Pro fyzikální reakci na dotyk/kurzor přidej modifikátor `.interactive(_:)`.
- **Morfování:** Seskupuj komponenty do `GlassEffectContainer` pro organické přechody.
- **Stíny:** Udržuj extrémně jemné (rádius 18, posun Y 8, opacita 0.18) – sklo si generuje vlastní optickou hloubku.
