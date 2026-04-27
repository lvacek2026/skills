---
name: grafana-energy-viz
description: Navrhuje a optimalizuje vizualizace energetických toků v Grafaně pro chytrou domácnost. Použij vždy, když uživatel zmíní Grafana dashboard pro FVE, fotovoltaiku, baterii, wallbox, smart home energetiku, Shelly, Loxone, Home Assistant, Victron nebo Tesla Powerwall styl vizualizace. Trigger také při požadavku na Canvas Panel, Sankey diagram, Solar Flow plugin, animaci toku energie ("marching ants"), nebo strukturování Flux/PromQL dotazů pro InfluxDB/Prometheus pro účely energetické vizualizace bez placených pluginů.
---

# Grafana Energy Flow Architect

Tento skill slouží k návrhu vysoce přehledných a funkčních energetických dashboardů v Grafaně s využitím **bezplatných** nástrojů jako Canvas Panel, Solar Flow plugin (`lehmannch-flow-panel`), Sankey Panel nebo Apache ECharts. Cílem je dosáhnout vizuální kvality srovnatelné s Tesla / Victron VRM bez nutnosti Enterprise licence.

## Hlavní instrukce pro model

Při návrhu vizualizace postupuj podle těchto priorit:

### 1. Volba nástroje podle případu užití

| Případ užití | Doporučený panel | Důvod |
|---|---|---|
| Real-time tok energie (Tesla / Victron styl) | **Canvas Panel** (nativní) nebo `lehmannch-flow-panel` | Podpora SVG, dynamických vlastností a animací |
| Historická analýza mixu zdrojů (odkud → kam) | **Sankey Panel** (`netsage-sankey-panel`) | Kvantifikuje toky mezi více zdroji a spotřebiči |
| Pokročilé animace (rotace, gradienty) | **Apache ECharts panel** (`volkovlabs-echarts-panel`) nebo Canvas s vlastním SVG z [draw.io](https://draw.io) | Plná kontrola nad SVG/JS |
| Okamžitý stav (overview) | **Stat panel** + **Gauge** | Rychlý přehled bez kognitivní zátěže |
| Trendová analýza | **Time series** s `Bars` nebo `Lines` | Standardní pohled na časovou řadu |

### 2. Barevná sémantika (závazný standard)

Zachovávej napříč všemi panely konzistentní barvy, aby uživatel rozpoznal stav bez čtení popisků:

- **Zelená / tyrkysová** (`#16a34a`, `#14b8a6`): produkce FVE, přebytky, nabíjení baterie
- **Modrá** (`#3b82f6`): spotřeba domácnosti, neutrální stav
- **Žlutá / oranžová** (`#f59e0b`, `#fb923c`): odběr ze sítě (import), varování před limitem jističe
- **Červená** (`#dc2626`): kritický stav, vybitá baterie, přetížení, přepětí
- **Šedá** (`#6b7280`): vypnutý / neaktivní stav

### 3. Animace toku energie

Pro efekt "tekoucí energie" (marching ants) navrhuj v Canvas Panelu / SVG následující CSS animaci:

```css
.flow-line {
  stroke: #16a34a;
  stroke-width: 4;
  fill: none;
  stroke-dasharray: 10 6;
  animation: dash 1s linear infinite;
}

@keyframes dash {
  to { stroke-dashoffset: -16; }
}
```

**Dynamická rychlost dle výkonu:** rychlost animace váž na hodnotu výkonu *P* [W] přes Data Links / Element Properties v Canvas Panelu. Doporučený mapping:

- `P < 100 W` → `animation-duration: 4s` (pomalu)
- `P 100–2000 W` → `animation-duration: 2s` (středně)
- `P > 2000 W` → `animation-duration: 0.5s` (rychle)
- `P = 0 W` → `animation: none` + barva šedá

**Směr toku:** záporné `stroke-dashoffset` = pohyb ve směru kreslení path. Pro obrácený tok použij kladnou hodnotu nebo `animation-direction: reverse`.

## Datové inženýrství

### Převod čítače energie (kWh) na okamžitý výkon (W)

Pokud uživatel pracuje s kumulativními čítači energie, automaticky navrhni transformaci na okamžitý výkon pomocí derivace:

$$P(t) = \frac{dE}{dt}$$

V praxi se v Grafaně počítá rozdílem hodnot mezi vzorky.

**Flux (InfluxDB 2.x):**

```flux
from(bucket: "homeassistant")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "kWh" and r._field == "energy_total")
  |> aggregateWindow(every: v.windowPeriod, fn: last, createEmpty: false)
  |> derivative(unit: 1h, nonNegative: true)
  |> map(fn: (r) => ({ r with _value: r._value * 1000.0 }))  // kWh/h → W
  |> yield(name: "power_W")
```

**PromQL (Prometheus):**

```promql
rate(home_energy_total_kwh[5m]) * 3600 * 1000  # kWh/s → W
```

### Sankey diagram – agregovaný energetický mix

Pro Sankey panel vytvoř dotaz, který vrátí trojici `source`, `target`, `value` (kWh za zvolené období):

```flux
import "experimental"

energy = from(bucket: "homeassistant")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._field == "energy_total")
  |> aggregateWindow(every: v.windowPeriod, fn: last, createEmpty: false)
  |> difference(nonNegative: true)
  |> sum()

// Výsledek pak v Transformations naformátuj na sloupce: source | target | value
```

## Pokyny pro design

- **Hierarchie dashboardů:** odděluj **Overview** (velké Stat panely pro okamžitý stav, max 1 obrazovka) od **Detail** dashboardů (časové řady, tabulky, analýza trendů). Drilldown řeš přes Data Links.
- **Jednotky:** **W / kW** pro výkon, **Wh / kWh** pro energii, **V** pro napětí, **A** pro proud, **%** pro SoC. Vždy nastav v poli *Unit* na panelu, nikdy neřeš násobky v dotazu, pokud nemusíš.
- **Prahy (thresholds) pro SoC baterie:**
  - 0–20 % červená
  - 20–50 % oranžová
  - 50–80 % žlutozelená
  - 80–100 % zelená
- **Mobilní zobrazení:** Canvas layout drž do ~50 prvků na panel a pracuj s relativním pozicováním (`%` místo `px`), aby zůstal čitelný na 4–6" displejích.
- **Refresh interval:** real-time panely 5–10 s, overview 30 s, historické dashboardy `Off` (uživatel řídí ručně).

## Příklady dotazů uživatele, které tento skill pokrývá

- "Jak udělám animovanou čáru mezi FVE a baterií v Canvasu?"
- "Napiš Flux query pro Sankey diagram, kde zdroje jsou FVE a Síť a spotřebiči Baterie, Domácnost a Wallbox."
- "Navrhni barevné prahy pro stav nabití baterie (SoC)."
- "Mám čítač kWh z Home Assistant, jak z něj v Grafaně udělám aktuální výkon ve W?"
- "Postav mi overview dashboard ve stylu Tesla Powerwall bez Enterprise pluginů."
- "Jak rozhýbat SVG schéma z draw.io v Grafana Canvas Panelu?"
