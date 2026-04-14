---
name: dehumidification-iot
description: Expertní logika pro řízení vysoušení přes IoT – fyzikální konstanty, predikce FVE, ochrana proti short-cyclingu. Použij při návrhu automatizace odvlhčování s fotovoltaikou.
triggers:
  - vysoušení
  - odvlhčování
  - dehumidification
  - short-cycling
  - FVE přebytek
  - solární řízení
  - Solcast
  - odvlhčovač
  - Dry režim
---

# Expertní logika řízení vysoušení přes IoT

Tento skill představuje expertní logiku, která propojuje fyzikální zákony odvlhčování s dynamikou fotovoltaické výroby. Jeho cílem je transformovat reaktivní spínání na proaktivní řízení založené na následujících znalostních pilířích a pravidlech.

## 1. Fyzikální časové konstanty (Kdy začíná skutečné vysoušení)

Expert ví, že proces separace vody není okamžitý a vyžaduje dodržení fází náběhu:

- **Fáze stabilizace (0–5 min):** Dochází k ochlazování výparníku pod rosný bod. Vlhkost začíná kondenzovat pouze v mikrovrstvě na lamelách.
- **Zahájení separace (5–12 min):** Kapky vody dosahují hmotnosti nutné k překonání povrchového napětí a začínají stékat do nádrže.
- **Plná účinnost (nad 20 min):** Zařízení dosahuje stabilního výkonu. Pro klimatizace v režimu Dry se doporučuje minimálně 15–20 minut běhu, pro kondenzační odvlhčovače minimálně 30 minut.

## 2. Ochrana před energetickými ztrátami a opotřebením

Skill striktně brání „short-cyclingu" (krátkým cyklům) z těchto důvodů:

- **Inrush current:** Start kompresoru spotřebuje nárazově desetinásobek běžného proudu, což namáhá střídač i baterii.
- **Re-evaporace:** Pokud se kompresor vypne dříve, než voda steče do nádrže, ventilátor odpaří vlhkost z lamel zpět do místnosti. Energetická efektivita takového cyklu je blízká nule.
- **Životnost:** Časté spínání kriticky opotřebovává kondenzátory a kontakty relé.

## 3. Logika „Look-Ahead" a predikce výroby

Místo sledování okamžitého výkonu skill pracuje s časovým oknem:

- **Pesimistický scénář (Estimate 10):** Algoritmus vyhodnocuje predikci na dalších 30 minut. Pokud i nejhorší očekávaný scénář (např. ze Solcastu) pokrývá příkon zařízení, teprve pak dojde ke startu.
- **Vazba na lokalitu (Police nad Metují):** Expert zohledňuje ranní mlhy a vysokou vlhkost, které způsobují pomalejší náběh výroby FVE a vyžadují konzervativnější přístup k aktivaci zátěží v dopoledních hodinách.
- **Baterie jako tlumič:** Pokud je SoC (stav nabití) dostatečné, skill dovolí „dotovat" běžící zařízení i během krátkého mraku, aby se dokončil efektivní 30minutový cyklus.

## 4. Hierarchie a rozhodovací matice

Skill prioritizuje zařízení podle jejich specifické efektivity:

- **Odvlhčovač (příkon 150–350 W):** Primární nástroj pro udržování vlhkosti. Vyfukuje vzduch o 3 až 5 stupňů teplejší, což zvyšuje efektivitu vysoušení v chladnějších prostorech.
- **Klimatizace v režimu Dry (příkon nad 900 W):** Spouští se pouze při vysokém solárním přebytku (nad 2 kW) a potřebě současného ochlazení prostoru.
- **Hystereze:** Aby se předešlo oscilacím, skill pracuje s odstupem (např. zapnutí při 60 % relativní vlhkosti, vypnutí při 50 %).

## 5. Persistence stavu (Znalost historie)

I po restartu řídicího systému (např. Home Assistant) si expert „pamatuje" čas posledního startu uložený v trvalé paměti. To zaručuje, že žádné zařízení nebude vypnuto v dalším kroku jen proto, že systém ztratil přehled o délce aktuálního běhu.
