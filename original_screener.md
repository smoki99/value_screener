# 📘 NASDAQ-100 Cheapest Quality Screener — Handbook

**Version 10** | Basierend auf Robert Novy-Marx: *"The Other Side of Value: The Gross Profitability Premium"* (2013)

---

## 📑 Inhaltsverzeichnis

1. [Überblick](#1-überblick)
2. [Akademischer Hintergrund](#2-akademischer-hintergrund)
3. [Installation & Quickstart](#3-installation--quickstart)
4. [Datenquellen](#4-datenquellen)
5. [Spalten-Referenz](#5-spalten-referenz)
6. [Farbschema](#6-farbschema)
7. [Scoring-Modelle](#7-scoring-modelle)
8. [Dezil-Ranking (Novy-Marx Methodik)](#8-dezil-ranking-novy-marx-methodik)
9. [Forward PEG Berechnung](#9-forward-peg-berechnung)
10. [Tabs im HTML-Report](#10-tabs-im-html-report)
11. [Rebalancing](#11-rebalancing)
12. [CLI-Optionen](#12-cli-optionen)
13. [Ausgabedateien](#13-ausgabedateien)
14. [Dateistruktur](#14-dateistruktur)
15. [Interpretation & Anwendung](#15-interpretation--anwendung)
16. [Limitierungen](#16-limitierungen)
17. [FAQ](#17-faq)
18. [Changelog](#18-changelog)

---

## 1. Überblick

Der **NASDAQ-100 Cheapest Quality Screener** kombiniert akademische Faktor-Forschung mit praktischem Screening. Er identifiziert Aktien, die sowohl **hohe Qualität** (profitable Unternehmen) als auch **günstige Bewertung** (niedriger PEG, niedriges P/B) aufweisen.

### Was der Screener tut

```
NASDAQ-100 Universum (102 Aktien)
        │
        ▼
┌─────────────────────────┐
│  Yahoo Finance Daten    │
│  • Fundamentaldaten     │
│  • Wachstumsschätzungen │
│  • Kursdaten            │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Berechnung             │
│  • GP/A, GM, ROE, P/B   │
│  • Forward & GAAP PEG   │
│  • Dezil-Ranking         │
│  • NM Score, MF Score   │
│  • Asset Growth         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Ausgabe                                │
│  • Terminal (farbige Tabellen)          │
│  • HTML Report (interaktiv, 6 Tabs)    │
│  • CSV Export                           │
└─────────────────────────────────────────┘
```

### Kernprinzip

> **"Profitable firms that are cheap earn the highest returns."**
> — Robert Novy-Marx, 2013

---

## 2. Akademischer Hintergrund

### 2.1 Das Paper

**Titel:** *"The Other Side of Value: The Gross Profitability Premium"*
**Autor:** Robert Novy-Marx
**Journal:** Journal of Financial Economics, Vol. 108, Issue 1, 2013, S. 1–28

### 2.2 Kernaussagen

| # | Aussage | Umsetzung im Screener |
|---|---------|----------------------|
| 1 | **Gross Profitability (GP/A)** ist ein starker Prädiktor für Aktienrenditen | ✅ GP/A als Kernfaktor (40% Gewicht im NM Score) |
| 2 | GP/A ist **komplementär zu Value** (B/M) — nicht redundant | ✅ P/B als Value-Komplement (35% Gewicht) |
| 3 | **Gross Profit** funktioniert besser als Net Income oder Operating Income | ✅ Wir verwenden Gross Profit, nicht Net Income für den Qualitätsfaktor |
| 4 | Der Premium bleibt nach Kontrolle für Market, Size, Value, Momentum bestehen | ✅ Momentum als dritter Faktor (25% Gewicht) |
| 5 | Kombination von Profitabilität + Value schlägt jeden Faktor allein | ✅ NM Rank = GP/A Dezil + P/B Dezil |

### 2.3 Warum Gross Profit und nicht Net Income?

```
Revenue                     ← Umsatz
 - Cost of Goods Sold       ← Direkte Kosten
═══════════════════════
= Gross Profit              ← DAS verwenden wir (÷ Total Assets = GP/A)
 - SG&A                     ← Oft Investitionen in Wachstum
 - R&D                      ← Investitionen in Innovation
 - Depreciation             ← Buchhalterisch, nicht cash-relevant
 - Interest                 ← Kapitalstruktur, nicht operativ
 - Taxes                    ← Steuerstrategie
═══════════════════════
= Net Income                ← Zu viel "Noise" für Qualitätsmessung
```

Novy-Marx argumentiert: SG&A und R&D sind häufig **Investitionen in zukünftige Profitabilität**.
Ein Unternehmen mit hohen R&D-Ausgaben hat niedrigeres Net Income, aber möglicherweise
bessere Zukunftsaussichten. Gross Profit erfasst die **echte operative Effizienz**.

### 2.4 Ergänzende Faktoren (über das Paper hinaus)

| Faktor | Quelle | Im Screener |
|--------|--------|-------------|
| Asset Growth | Cooper, Gulen & Schill (2008) | ✅ AG Spalte |
| Earnings Quality | Sloan (1996) | ❌ Nicht implementiert |
| ROE | Haugen & Baker (1996) | ✅ ROE Spalte + MF Score |
| PEG Ratio | Peter Lynch | ✅ fPEG + gPEG |
| Momentum | Jegadeesh & Titman (1993) | ✅ 6M + 12M |

---

## 3. Installation & Quickstart

### 3.1 Voraussetzungen

```bash
Python 3.8+
pip install yfinance pandas tabulate requests
```

### 3.2 Dateien

```
project/
├── nasdaq100_quality_value.py   # Hauptskript (Logik + Terminal)
├── html_template.py             # HTML/CSS/JS Template
└── HANDBOOK.md                  # Dieses Handbuch
```

### 3.3 Quickstart

```bash
# Erste Ausführung (lädt alle Daten von Yahoo Finance, ~3-5 Min)
python nasdaq100_quality_value.py

# Folgende Ausführungen nutzen Cache (<5 Sek)
python nasdaq100_quality_value.py

# Cache löschen und neu laden
python nasdaq100_quality_value.py --clear-cache

# Ohne Farben (für Pipe/Redirect)
python nasdaq100_quality_value.py --no-color > output.txt

# Hilfe
python nasdaq100_quality_value.py --help
```

### 3.4 Generierte Ausgabedateien

```bash
# Nach der Ausführung:
nasdaq100_screener.html          # Interaktiver HTML-Report (im Browser öffnen)
nasdaq100_cheapest_quality.csv   # CSV für Excel/Google Sheets
nasdaq100_cache.db               # SQLite Cache (automatisch)
```

---

## 4. Datenquellen

### 4.1 Ticker-Liste

- **Quelle:** Wikipedia — [Nasdaq-100](https://en.wikipedia.org/wiki/Nasdaq-100)
- **Deduplizierung:** GOOGL (Duplikat von GOOG) und FOXA (Duplikat von FOX) werden entfernt
- **Cache:** 24 Stunden

### 4.2 Fundamentaldaten

| Datenpunkt | Yahoo Finance Accessor | Verwendung |
|------------|----------------------|------------|
| Gross Profit | `stock.financials['Gross Profit']` | GP/A, GM |
| Total Revenue | `stock.financials['Total Revenue']` | GM |
| Total Assets | `stock.balance_sheet['Total Assets']` | GP/A, AG |
| Net Income | `stock.financials['Net Income']` | GAAP PEG |
| Forward PE | `stock.info['forwardPE']` | Forward PEG |
| Trailing PE | `stock.info['trailingPE']` | GAAP PEG |
| ROE | `stock.info['returnOnEquity']` | ROE, MF Score |
| P/B | `stock.info['priceToBook']` | P/B, Dezil, NM Score |
| Earnings Growth | `stock.info['earningsGrowth']` | Fallback für PEG |

### 4.3 Wachstumsschätzungen (Priorisierung)

```
Priorität 1: stock.growth_estimates['stockTrend']
             → 2-Jahres-Blend aus 0y + +1y (geometrisches Mittel)
             → Quelle: "GE-2Y"

Priorität 2: stock.earnings_estimate['growth']
             → 2-Jahres-Blend aus 0y + +1y
             → Quelle: "EE-2Y"

Priorität 3: stock.info['earningsGrowth']
             → 1-Jahres-Wachstum mit Dämpfung
             → Quelle: "1Y→info-eGr"

Fallback:    Kein PEG berechenbar → "N/A"
```

### 4.4 Cache

- **Technologie:** SQLite (`nasdaq100_cache.db`)
- **Max. Alter:** 24 Stunden (konfigurierbar via `CACHE_MAX_AGE_HOURS`)
- **Inhalt:** info, financials, balance_sheet, history, growth_estimates pro Ticker
- **Erste Ausführung:** ~3-5 Minuten (API-Calls mit 0.5s Delay)
- **Folgende:** <5 Sekunden (aus Cache)

---

## 5. Spalten-Referenz

### 5.1 Fundamentaldaten

| Spalte | Vollständiger Name | Formel | Bedeutung |
|--------|--------------------|--------|-----------|
| **GP/A** | Gross Profitability / Assets | `Gross Profit ÷ Total Assets` | Novy-Marx Kernfaktor: Wie effizient nutzt das Unternehmen seine Assets, um Bruttogewinn zu erzeugen? |
| **GM** | Gross Margin | `Gross Profit ÷ Total Revenue` | Bruttomarge: Wie viel Gewinn bleibt pro Dollar Umsatz nach direkten Kosten? Indikator für Pricing Power und Moat. |
| **ROE** | Return on Equity | `Net Income ÷ Shareholders' Equity` | Eigenkapitalrendite: Wie profitabel setzt das Unternehmen Eigenkapital ein? |
| **P/B** | Price-to-Book | `Market Cap ÷ Book Value` | Kurs-Buchwert-Verhältnis: Wie teuer ist die Aktie relativ zum Buchwert? Invertiertes B/M (Book-to-Market). |

### 5.2 Scoring

| Spalte | Vollständiger Name | Berechnung | Bedeutung |
|--------|--------------------|------------|-----------|
| **NM** | Novy-Marx Score | GP/A (40%) + P/B (35%) + Momentum (25%) | Gewichteter Qualitäts-Score nach Novy-Marx (0–5) |
| **NM★** | Novy-Marx Sterne | Gerundeter NM Score als Sterne | Visuelle Darstellung |
| **MF** | Multi-Factor Score | GP/A (25%) + ROE (20%) + P/B (20%) + fPEG (15%) + Mom (20%) | Erweiterter Score mit mehr Faktoren (0–5) |
| **MF★** | Multi-Factor Sterne | Gerundeter MF Score als Sterne | Visuelle Darstellung |
| **Qual** | Qualitätsstufe | max(NM, MF) → ★★★/★★/★/— | Zusammenfassung: ★★★ ≥4.5, ★★ ≥3.5, ★ ≥2.5 |

### 5.3 Bewertung (PEG)

| Spalte | Vollständiger Name | Formel | Bedeutung |
|--------|--------------------|--------|-----------|
| **fPEG** | Forward PEG | `Forward PE ÷ (Growth% × 100)` | Vorwärtsgerichtetes PEG basierend auf Analysten-Wachstumsschätzungen. <1 = günstig. |
| **gPEG** | GAAP PEG | `Trailing PE ÷ (historische Net Income CAGR × 100)` | Rückwärtsgerichtetes PEG basierend auf tatsächlichem Gewinnwachstum. |
| **Grw%** | Growth Prozent | Verwendetes Wachstum für fPEG | Das Wachstum, das in die fPEG-Berechnung eingeflossen ist. |
| **Src** | Source / Quelle | GE-2Y, EE-2Y, GE-1Y, 1Y→info-eGr | Woher die Wachstumsschätzung stammt (siehe Abschnitt 4.3). |
| **Zone** | Bewertungszone | fPEG → 🟢/🟡/🔴 | Schnelle visuelle Einordnung der Bewertung. |

### 5.4 Dezil-Ranking (Novy-Marx)

| Spalte | Vollständiger Name | Berechnung | Bedeutung |
|--------|--------------------|------------|-----------|
| **D.GP** | Decile Gross Profitability | Perzentil-Rang von GP/A im Universum → Dezil 1–10 | Relative Position der GP/A innerhalb aller NASDAQ-100 Aktien. 10 = Top 10% (beste Profitabilität). |
| **D.PB** | Decile Price-to-Book | Perzentil-Rang von P/B im Universum → Dezil 1–10 (invertiert) | Relative Position der Bewertung. 10 = günstigste 10% (niedrigstes P/B). |
| **NMR** | Novy-Marx Rank | `D.GP + D.PB` | Kombinierter Rang (2–20). Kernidee des Papers: **Profitable UND günstige Aktien haben die höchsten Renditen.** 20 = perfekt, 2 = schlecht. |

### 5.5 Zusätzliche Faktoren

| Spalte | Vollständiger Name | Formel | Bedeutung |
|--------|--------------------|--------|-----------|
| **AG** | Asset Growth | `(Total Assets aktuell - Total Assets Vorjahr) ÷ Total Assets Vorjahr` | Jährliches Wachstum der Bilanzsumme. Novy-Marx und Cooper et al. (2008) zeigen: **Hohes Asset Growth → niedrigere zukünftige Renditen.** |
| **6M** | 6-Monats-Performance | Kursänderung letzte 6 Monate | Kurzfristiges Momentum |
| **12M** | 12-Monats-Performance | Kursänderung letzte 12 Monate | Langfristiges Momentum (verwendet im NM und MF Score) |

---

## 6. Farbschema

### 6.1 Übersicht

Alle Farben folgen dem Ampelprinzip: **Grün = Gut, Gelb = OK, Rot = Warnung.**

| Spalte | 🟢 Grün | 🟡 Gelb | 🔴 Rot | Logik |
|--------|---------|---------|--------|-------|
| **GP/A** | ≥ 30% | 15–30% | < 15% | Novy-Marx: >30% = hohe Asset-Effizienz |
| **GM** | ≥ 50% | 30–50% | < 30% | Hohe Marge = Pricing Power / Moat |
| **ROE** | ≥ 20% | 10–20% | < 10% | Buffett/Novy-Marx: >20% = exzellente Kapitalrendite |
| **P/B** | ≤ 5 | 5–15 | > 15 | Invertiert: niedriges P/B = günstige Bewertung |
| **fPEG** | ≤ 1.0 | 1.0–1.5 | > 1.5 | Peter Lynch: PEG <1 = unterbewertet |
| **gPEG** | ≤ 1.0 | 1.0–1.5 | > 1.5 | Gleiches Schema für historischen PEG |
| **AG** | ≤ 10% | 10–25% | > 25% | Invertiert: niedriges Wachstum = besser für Renditen |
| **D.GP** | 8–10 | 4–7 | 1–3 | Top-Dezile = beste Profitabilität im Universum |
| **D.PB** | 8–10 | 4–7 | 1–3 | Top-Dezile = günstigste Bewertung im Universum |
| **NMR** | 16–20 | 10–15 | < 10 | Hoher kombinierter Rang = profitabel UND günstig |
| **6M/12M** | ≥ 0% | — | < 0% | Positives vs. negatives Momentum |

### 6.2 Farben im Terminal (ANSI)

```
Grün:  \033[92m
Gelb:  \033[93m
Rot:   \033[91m
Reset: \033[0m
```

Deaktivierbar mit `--no-color`.

### 6.3 Farben im HTML (CSS)

```css
.c-green  { color: #3fb950; }   /* Fundamentaldaten */
.c-yellow { color: #d29922; }
.c-red    { color: #f85149; }
.peg-green  { color: #3fb950; font-weight: 600; }  /* PEG (fett) */
.peg-yellow { color: #d29922; font-weight: 600; }
.peg-red    { color: #f85149; font-weight: 600; }
.perf-pos { color: #3fb950; }   /* Performance */
.perf-neg { color: #f85149; }
```

---

## 7. Scoring-Modelle

### 7.1 Star Rating (Basis für beide Scores)

Jeder Faktor wird in 1–5 Sterne umgerechnet:

#### GP/A Sterne

| GP/A | Sterne |
|------|--------|
| < 10% | ⭐ |
| 10–20% | ⭐⭐ |
| 20–30% | ⭐⭐⭐ |
| 30–40% | ⭐⭐⭐⭐ |
| ≥ 40% | ⭐⭐⭐⭐⭐ |

#### ROE Sterne

| ROE | Sterne |
|-----|--------|
| < 0% | ⭐ (Strafpunkt) |
| 0–5% | ⭐ |
| 5–10% | ⭐⭐ |
| 10–20% | ⭐⭐⭐ |
| 20–30% | ⭐⭐⭐⭐ |
| ≥ 30% | ⭐⭐⭐⭐⭐ |

#### P/B Sterne (invertiert — niedriger = besser)

| P/B | Sterne |
|-----|--------|
| > 40 | ⭐ |
| 20–40 | ⭐⭐ |
| 10–20 | ⭐⭐⭐ |
| 5–10 | ⭐⭐⭐⭐ |
| ≤ 5 | ⭐⭐⭐⭐⭐ |

#### Forward PEG Sterne (invertiert)

| fPEG | Sterne |
|------|--------|
| > 2.5 | ⭐ |
| 2.0–2.5 | ⭐⭐ |
| 1.5–2.0 | ⭐⭐⭐ |
| 1.0–1.5 | ⭐⭐⭐⭐ |
| ≤ 1.0 | ⭐⭐⭐⭐⭐ |

#### Momentum (12M) Sterne

| 12M Perf | Sterne |
|----------|--------|
| < 0% | ⭐ |
| 0–10% | ⭐⭐ |
| 10–25% | ⭐⭐⭐ |
| 25–50% | ⭐⭐⭐⭐ |
| ≥ 50% | ⭐⭐⭐⭐⭐ |

### 7.2 Novy-Marx Score (NM)

```
NM = GP/A★ × 0.40 + P/B★ × 0.35 + Momentum★ × 0.25
     ─────────────   ────────────   ─────���────────────
     Qualität         Value          Momentum
```

**Besonderheiten:**
- Mindestens 2 von 3 Faktoren müssen verfügbar sein
- Bei P/B★ = 1 (sehr teuer): NM wird auf max. 3.0 gedeckelt
- Fehlende Faktoren: -0.15 Abzug pro fehlendem Faktor

### 7.3 Multi-Factor Score (MF)

```
MF = GP/A★ × 0.25 + ROE★ × 0.20 + P/B★ × 0.20 + fPEG★ × 0.15 + Mom★ × 0.20
     ─────────────   ────────────   ────────────   ─────────────   ─────────────
     Qualität         Profitabilität  Value         Bewertung       Momentum
```

**Besonderheiten:**
- Mindestens 2 von 5 Faktoren müssen verfügbar sein
- Bei P/B★ = 1: MF wird auf max. 3.0 gedeckelt
- Bei fPEG★ = 1 UND GP/A★ ≤ 3: MF wird auf max. 3.0 gedeckelt
- Fehlende Faktoren: -0.15 Abzug pro fehlendem Faktor

### 7.4 Qualitätsstufe (Qual)

| Best of (NM, MF) | Qualitätsstufe | Bedeutung |
|-------------------|----------------|-----------|
| ≥ 4.5 | ★★★ | Exzellent — Top-Qualität in fast allen Faktoren |
| ≥ 3.5 | ★★ | Gut — Solide Qualität, Kandidat für Sweet Spot |
| ≥ 2.5 | ★ | Durchschnittlich — Einige Schwächen |
| < 2.5 | — | Niedrig — Vorsicht, potenzielle Value Trap |

---

## 8. Dezil-Ranking (Novy-Marx Methodik)

### 8.1 Warum Dezile statt absoluter Schwellenwerte?

Novy-Marx sortiert Aktien nicht nach festen Grenzen (z.B. "GP/A > 30% = gut"),
sondern nach ihrer **relativen Position im Universum**. Das ist wichtig, weil:

- Im NASDAQ-100 haben die meisten Aktien GP/A > 15% — das ist schon überdurchschnittlich vs. Gesamtmarkt
- Absolute Schwellenwerte passen sich nicht an das Universum an
- Dezile zeigen: "Ist diese Aktie **innerhalb dieser Gruppe** profitabel/günstig?"

### 8.2 Berechnung

```python
# GP/A Dezil (höher = profitabler = besser)
1. Alle GP/A Werte im Universum sortieren
2. Perzentil berechnen: rank / total
3. Dezil = min(10, int(perzentil × 10) + 1)
→ Dezil 10 = Top 10%, Dezil 1 = Bottom 10%

# P/B Dezil (niedriger P/B = günstiger = besser → invertiert)
1. Alle P/B Werte im Universum sortieren
2. Perzentil berechnen: Anteil mit P/B ≥ eigener P/B
3. Dezil = min(10, int(perzentil × 10) + 1)
→ Dezil 10 = günstigste 10%, Dezil 1 = teuerste 10%

# Momentum Dezil (höher = stärkeres Momentum = besser)
1. Alle 12M-Performance Werte sortieren
2. Perzentil berechnen: rank / total
3. Dezil = min(10, int(perzentil × 10) + 1)
```

### 8.3 NM Rank (Novy-Marx Combined Rank)

```
NMR = D.GP + D.PB
Range: 2 (schlecht) bis 20 (perfekt)
```

| NMR | Interpretation | Beispiel |
|-----|---------------|----------|
| **18–20** | 🟢 Top Pick: Profitabel UND günstig | GP/A Top-Dezil + P/B günstigstes Dezil |
| **14–17** | 🟢 Stark: Gute Kombination | Überdurchschnittlich in beiden |
| **10–13** | 🟡 Mittel: Ein Faktor stark, einer schwach | Hohe GP/A aber teuer, oder günstig aber wenig profitabel |
| **6–9** | 🔴 Schwach: Unterdurchschnittlich | Weder besonders profitabel noch günstig |
| **2–5** | 🔴 Vermeiden: Bottom in beiden | Niedrige Profitabilität UND teuer |

### 8.4 Unterschied zu NM Score

| | NM Score | NMR (NM Rank) |
|---|---------|---------------|
| **Basis** | Absolute Star Ratings (1–5) | Relative Dezil-Position (1–10) |
| **Faktoren** | GP/A + P/B + Momentum | Nur GP/A + P/B |
| **Range** | 0–5 | 2–20 |
| **Vorteil** | Berücksichtigt Momentum | Treuer zum Paper (relative Sortierung) |
| **Verwendung** | Sweet Spot Filter | NM Rank Tab, Paper-nahe Analyse |

Beide Scores werden angezeigt — sie ergänzen sich.

---

## 9. Forward PEG Berechnung

### 9.1 Datenquellen-Kaskade

```
┌─────────────────────────────────────────────┐
│ Priorität 1: growth_estimates (GE)          │
│ → 2-Jahres-Blend: √((1+g_0y) × (1+g_1y))-1│
│ → Quelle: "GE-2Y"                          │
│ → Cap: 60%                                  │
├─────────────────────────────────────────────┤
│ Priorität 2: earnings_estimate (EE)         │
│ → 2-Jahres-Blend (gleiche Formel)           │
│ → Quelle: "EE-2Y"                          │
│ → Cap: 60%                                  │
├─────────────────────────────────────────────┤
│ Priorität 3: info['earningsGrowth']         │
│ → 1-Jahres mit progressiver Dämpfung        │
│ → Quelle: "1Y→info-eGr"                    │
│ → Dämpfung + Cap: 50%                      │
├─────────────────────────────────────────────┤
│ Fallback: Kein PEG berechenbar              │
│ → fPEG = N/A                               │
└─────────────────────────────────────────────┘
```

### 9.2 Dämpfungsformel (nur für 1-Jahres-Wachstum aus info)

```
dampened = min(growth, 0.30) + max(0, growth - 0.30) × 0.2
dampened = min(dampened, 0.50)  # Hard Cap

Beispiele:
  earningsGrowth  20% → dampened  20% (unverändert)
  earningsGrowth  50% → dampened  34% (30% + 4%)
  earningsGrowth 100% → dampened  44% (30% + 14%)
  earningsGrowth 300% → dampened  50% (Cap erreicht)
```

**Warum Dämpfung?** 1-Jahres-Wachstum ist volatil und oft nicht nachhaltig.
Analysten-Consensus (GE/EE) über 2 Jahre ist zuverlässiger und wird daher nicht gedämpft.

### 9.3 GAAP PEG (gPEG)

```
gPEG = Trailing PE ÷ (Net Income CAGR × 100)

CAGR = (Net Income aktuell ÷ Net Income ältestes)^(1/Jahre) - 1
```

Verwendet historisches Gewinnwachstum aus den Jahresabschlüssen (bis zu 4 Jahre).
Nur berechenbar wenn Net Income in allen Jahren positiv war.

---

## 10. Tabs im HTML-Report

### 10.1 Alle Aktien

**Sortierung:** Forward PEG aufsteigend (günstigste zuerst)
**Inhalt:** Alle ~100 NASDAQ-100 Aktien mit allen Spalten
**Suchfunktion:** ✅ Nach Symbol oder Name

### 10.2 💎 Sweet Spot

**Filter:** fPEG vorhanden UND (NM ≥ 3.5 ODER MF ≥ 3.5)
**Sortierung:** Forward PEG aufsteigend
**Bedeutung:** Die **besten Kandidaten** — günstige Bewertung kombiniert mit hoher Qualität.
Dies ist der wichtigste Tab für Anlageentscheidungen.

### 10.3 📊 NM Rank

**Filter:** NMR vorhanden (alle Aktien mit GP/A und P/B)
**Sortierung:** NMR absteigend (höchster Rang zuerst)
**Bedeutung:** Rein nach Novy-Marx Methodik sortiert — unabhängig vom PEG.
Zeigt welche Aktien **relativ zum NASDAQ-100 Universum** am profitabelsten UND günstigsten sind.

### 10.4 ⚠️ Value Traps

**Filter:** fPEG vorhanden UND NM < 2.5 UND MF < 2.5
**Sortierung:** Forward PEG aufsteigend
**Bedeutung:** **Warnung!** Diese Aktien erscheinen günstig (niedriger PEG),
haben aber schlechte Qualitätsscores. Typische Value Traps — billig aus gutem Grund.

### 10.5 🔍 PEG Divergenz

**Filter:** |fPEG/gPEG Ratio| < 0.5 oder > 2.0
**Sortierung:** Nach Ratio
**Bedeutung:** Aktien wo Forward PEG und GAAP PEG stark auseinanderlaufen:
- **📈 Bullish (fPEG << gPEG):** Analysten erwarten Beschleunigung des Wachstums
- **📉 Bearish (fPEG >> gPEG):** Analysten erwarten Verlangsamung

### 10.6 📊 Kein PEG

**Filter:** fPEG = N/A
**Sortierung:** NM Score absteigend
**Bedeutung:** Aktien ohne berechenbaren Forward PEG (negatives Wachstum, fehlende Daten).
Sortiert nach Qualität — die Top-Aktien hier könnten Turnaround-Kandidaten sein.

---

## 11. Rebalancing

### 11.1 Novy-Marx Empfehlung

Das Paper verwendet **jährliches Rebalancing im Juni/Juli** nach Veröffentlichung
der Jahresdaten (Fiscal Year Ends meist im Dezember, Filings bis April/Mai).

### 11.2 Screener-Hinweis

Der Screener zeigt automatisch einen Rebalancing-Hinweis:

```
März:  📅 Nächstes Rebalancing: Juli
Juni:  🔄 REBALANCING-FENSTER: Juni/Juli — Novy-Marx empfiehlt jährliches Rebalancing jetzt!
Juli:  🔄 REBALANCING-FENSTER: Juni/Juli — Novy-Marx empfiehlt jährliches Rebalancing jetzt!
Aug:   📅 Nächstes Rebalancing: Juli nächstes Jahr
```

### 11.3 Praktische Empfehlung

| Frequenz | Verwendung |
|----------|-----------|
| **Täglich/Wöchentlich** | Screener laufen lassen, Watchlist pflegen |
| **Monatlich** | Neue Kandidaten prüfen, größere Shifts identifizieren |
| **Jährlich (Juni/Juli)** | Portfolio rebalancieren nach Paper-Methodik |

---

## 12. CLI-Optionen

```
python nasdaq100_quality_value.py [OPTIONEN]

Optionen:
  --clear-cache    SQLite Cache löschen und alle Daten neu laden
  --no-color       ANSI-Farbcodes deaktivieren (für Pipe/Redirect)
  --help, -h       Hilfe anzeigen
```

### Beispiele

```bash
# Standard: Cache nutzen, farbige Ausgabe
python nasdaq100_quality_value.py

# Frische Daten erzwingen
python nasdaq100_quality_value.py --clear-cache

# Output in Datei (ohne ANSI-Codes)
python nasdaq100_quality_value.py --no-color > report.txt

# Nur Cache löschen, nicht neu laden
python nasdaq100_quality_value.py --clear-cache && echo "Cache gelöscht"
```

---

## 13. Ausgabedateien

### 13.1 Terminal

Farbige Tabellen mit `tabulate` (psql Format). Enthält 5 Tabellen:

1. **Haupttabelle** — Alle Aktien sortiert nach fPEG
2. **💎 Sweet Spot** — Günstig + hohe Qualität
3. **📊 NM Rank** — Nach Novy-Marx Dezil-Rang
4. **⚠️ Value Traps** — Günstig aber schlechte Qualität
5. **📊 Kein PEG** — Kein Forward PEG verfügbar

### 13.2 HTML Report (`nasdaq100_screener.html`)

- **Interaktiv:** Klick auf Spaltenheader zum Sortieren
- **Suchbar:** Echtzeit-Suche nach Symbol oder Name
- **6 Tabs:** Alle Aktien, Sweet Spot, NM Rank, Value Traps, PEG Divergenz, Kein PEG
- **Stats Bar:** Zusammenfassung der Key Metrics
- **Dark Theme:** GitHub-inspiriertes Dark UI
- **Standalone:** Keine externen Dependencies, alles inline

### 13.3 CSV Export (`nasdaq100_cheapest_quality.csv`)

Spalten: Symbol, Name, GP/A, GM, ROE, P/B, NM, MF, Qual, fPEG, gPEG,
Grw%, Src, Zone, D.GP, D.PB, NMR, AG, 6M, 12M

Ohne Farbcodes — geeignet für Excel, Google Sheets, weitere Analyse.

---

## 14. Dateistruktur

```
project/
├── nasdaq100_quality_value.py   # Hauptskript
│   ├── Color                    # ANSI-Farbcodes
│   ├── colorize_*()             # Terminal-Farbfunktionen (7 Stück)
│   ├── init_db()                # SQLite Cache Setup
│   ├── fetch_growth_estimates() # Wachstumsdaten-Kaskade
│   ├── calculate_performance()  # 6M/12M Performance
│   ├── calculate_asset_growth() # YoY Asset Growth
│   ├── get_star_rating()        # Universal Star Rating
│   ├── calculate_forward_peg()  # Forward PEG mit Dämpfung
│   ├── calculate_gaap_peg()     # Historischer PEG
│   ├── score_novy_marx()        # NM Score (3 Faktoren)
│   ├── score_multi_factor()     # MF Score (5 Faktoren)
│   ├── add_percentile_ranks()   # Dezil-Ranking
│   ├── compute_metrics()        # Alle Metriken pro Aktie
│   ├── build_unified_row()      # Terminal-Zeile mit Farben
│   ├── generate_html_report()   # HTML via Template
│   └── analyze_nasdaq100()      # Hauptfunktion
│
├── html_template.py             # HTML/CSS/JS Template
│   ├── HTML_TEMPLATE            # Komplettes HTML als String
│   └── render_html()            # Template-Renderer ({{KEY}} → Wert)
│
├── HANDBOOK.md                  # Dieses Handbuch
│
└── (generiert)
    ├── nasdaq100_cache.db       # SQLite Cache
    ├── nasdaq100_screener.html  # Interaktiver HTML-Report
    └── nasdaq100_cheapest_quality.csv  # CSV Export
```

---

## 15. Interpretation & Anwendung

### 15.1 Den perfekten Pick finden

Ein idealer Novy-Marx Pick hat:

```
✅ GP/A ≥ 30%        (grün)     → Hohe Asset-Effizienz
✅ GM ≥ 50%           (grün)     → Pricing Power / Moat
✅ ROE ≥ 20%          (grün)     → Starke Kapitalrendite
✅ P/B ≤ 5            (grün)     → Günstige Bewertung
✅ fPEG ≤ 1.0         (grün)     → Unterbewertet für Wachstum
✅ D.GP ≥ 8           (grün)     → Top-Dezil Profitabilität
✅ D.PB ≥ 8           (grün)     → Top-Dezil Bewertung
✅ NMR ≥ 16           (grün)     → Novy-Marx Sweet Spot
✅ AG ≤ 10%           (grün)     → Konservatives Wachstum
✅ 12M > 0%           (grün)     → Positives Momentum
```

**Realität:** Keine Aktie erfüllt alle Kriterien. Das Ziel ist die **beste Kombination**.

### 15.2 Typische Muster

#### 🏆 Quality Compounder (z.B. NVDA, ADBE, GOOG)
```
GP/A: 🟢 hoch    GM: 🟢 hoch    ROE: 🟢 hoch
P/B:  🔴 teuer   fPEG: 🟢 günstig (hohes Wachstum kompensiert)
NMR:  🟡 mittel  AG: 🟡 mittel
→ Qualität top, Value mittel. fPEG entscheidend!
```

#### 💎 Value + Quality (z.B. CMCSA, CHTR)
```
GP/A: 🟢 hoch    GM: 🟢 hoch    ROE: 🟢 hoch
P/B:  🟢 günstig fPEG: 🟢 günstig
NMR:  🟢 hoch    AG: 🟢 niedrig
→ Perfekter Novy-Marx Pick! Aber: warum so günstig? Prüfen!
```

#### ⚠️ Value Trap (z.B. niedrige Qualität + günstiger PEG)
```
GP/A: 🔴 niedrig GM: 🟡 mittel  ROE: 🔴 niedrig
P/B:  🟢 günstig fPEG: 🟢 günstig
NMR:  🔴 niedrig AG: 🔴 hoch
→ Günstig aus gutem Grund! Finger weg.
```

#### 🚀 Momentum Play (z.B. hohes Wachstum aber teuer)
```
GP/A: 🟢 hoch    GM: 🟢 hoch    ROE: 🟢 hoch
P/B:  🔴 teuer   fPEG: 🔴 teuer
NMR:  🔴 niedrig AG: 🔴 hoch
→ Alles eingepreist. Nur kaufen bei Überzeugung.
```

### 15.3 Checkliste vor dem Kauf

1. **Sweet Spot Tab prüfen** — Ist die Aktie dort gelistet?
2. **NMR ≥ 14** — Gute relative Position in Profitabilität + Value?
3. **AG prüfen** — Warnung bei AG > 25% (Asset Growth zu hoch)?
4. **fPEG vs. gPEG vergleichen** — Divergenz? Bullish oder Bearish Signal?
5. **12M Momentum** — Negativer Trend? Warum?
6. **Qualitative Analyse** — Der Screener ersetzt keine Unternehmensanalyse!

### 15.4 Was der Screener NICHT kann

- ❌ Zukunft vorhersagen
- ❌ Branchenrisiken bewerten (Regulierung, Disruption)
- ❌ Management-Qualität einschätzen
- ❌ Makro-Risiken berücksichtigen (Zinsen, Rezession)
- ❌ Timing-Empfehlungen geben

---

## 16. Limitierungen

### 16.1 Universum

| Limitation | Impact | Mitigation |
|-----------|--------|-----------|
| Nur NASDAQ-100 | Keine Small/Mid Caps, keine internationalen Aktien | Paper zeigte stärksten Effekt bei Small Caps |
| ~100 Aktien | Dezile = ~10 Aktien pro Gruppe (wenig statistisch) | Besser als absolute Schwellenwerte |
| Tech-lastig | NASDAQ-100 ist von Natur aus Tech-übergewichtet | Sektorbias beachten |

### 16.2 Daten

| Limitation | Impact | Mitigation |
|-----------|--------|-----------|
| Yahoo Finance Daten | Gelegentlich fehlende oder fehlerhafte Daten | Fallback-Kaskade, Error Handling |
| Analysten-Consensus | Kann systematisch zu optimistisch sein | Dämpfung bei 1Y-Daten, Cap bei 60% |
| Historische Financials | Max 4 Jahre für GAAP PEG | Ausreichend für CAGR |
| Quartals- vs. Jahresdaten | Mix möglich | Yahoo Finance normalisiert automatisch |

### 16.3 Methodik

| Limitation | Impact | Mitigation |
|-----------|--------|-----------|
| P/B statt B/M | Invertiert, kann bei Buybacks abweichen | Für Large Caps vernachlässigbar |
| Kein Short-Leg | Paper testet Long/Short, wir nur Long | Für Retail-Anleger normal |
| Keine Transaktionskosten | Rebalancing-Kosten nicht berücksichtigt | Bei jährlichem Rebalancing gering |
| Keine Sektorbereinigung | Tech-Bias im GP/A Ranking | Bewusste Entscheidung für Einfachheit |

---

## 17. FAQ

### Wie oft sollte ich den Screener laufen lassen?

**Wöchentlich** für die Watchlist, **monatlich** für ernsthafte Analyse,
**jährlich im Juni/Juli** für Portfolio-Rebalancing.

### Warum hat NVDA einen niedrigen NMR aber hohen NM Score?

NMR basiert NUR auf GP/A Dezil + P/B Dezil (relativ). NVDA hat sehr hohes P/B (teuer → niedriges D.PB),
auch wenn GP/A top ist. NM Score berücksichtigt zusätzlich Momentum, was bei NVDA stark ist.

### Was bedeutet "1Y→info-eGr" als Quelle?

Die Wachstumsschätzung stammt aus `stock.info['earningsGrowth']` (Yahoo Finance),
einem 1-Jahres-Wert, der mit progressiver Dämpfung verwendet wird.
Weniger zuverlässig als 2-Jahres-Analysten-Consensus (GE-2Y).

### Warum wird Asset Growth negativ bewertet?

Cooper, Gulen & Schill (2008) zeigten: Unternehmen mit hohem Asset Growth
(viele Akquisitionen, hohe Investitionen) haben **niedrigere zukünftige Renditen**.
Mögliche Erklärung: Overpayment für Akquisitionen, Empire Building.

### Kann ich andere Universen als NASDAQ-100 verwenden?

Theoretisch ja — die Logik ist universell. Sie müssten nur `get_nasdaq100_tickers()`
ersetzen (z.B. S&P 500, Russell 1000, DAX).

### Warum GP/A und nicht Operating Margin?

Novy-Marx testet explizit verschiedene Profitabilitätsmaße. Gross Profit / Assets
hat die höchste Vorhersagekraft für zukünftige Renditen, weil SG&A und R&D
oft Investitionen in zukünftige Profitabilität sind (siehe Abschnitt 2.3).

### Was tun wenn viele Aktien "N/A" bei fPEG zeigen?

Prüfen Sie den **NM Rank Tab** — dort werden Aktien rein nach Qualität + Value
sortiert, unabhängig von Wachstumsschätzungen.

---

## 18. Changelog

### v10 (aktuell)
- ✅ Dezil-Ranking (D.GP, D.PB, NMR) nach Novy-Marx Methodik
- ✅ Asset Growth (AG) als Warnindicator
- ✅ NM Rank Tab im HTML-Report
- ✅ Rebalancing-Hinweis (Juni/Juli)
- ✅ HTML Template ausgelagert (`html_template.py`)
- ✅ Farbschema für alle Fundamentaldaten (GP/A, GM, ROE, P/B)

### v9
- ✅ Gross Margin (GM) Spalte hinzugefügt
- ✅ Farbcodes für GP/A, GM, ROE, P/B
- ✅ HTML Report mit Dark Theme

### v8
- ✅ 2-Jahres Growth Blend (GE-2Y, EE-2Y)
- ✅ Growth Estimates Kaskade
- ✅ Progressive Dämpfung für 1Y-Wachstum
- ✅ PEG Divergenz Tab

### v7
- ✅ SQLite Cache
- ✅ HTML Report mit Tabs
- ✅ CSV Export

### v1–v6
- Iterative Entwicklung
- NM Score, MF Score
- Star Ratings
- Forward & GAAP PEG

---

## 📚 Literatur

1. **Novy-Marx, R.** (2013). *The Other Side of Value: The Gross Profitability Premium.* Journal of Financial Economics, 108(1), 1–28.
2. **Cooper, M., Gulen, H., & Schill, M.** (2008). *Asset Growth and the Cross-Section of Stock Returns.* Journal of Finance, 63(4), 1609–1651.
3. **Fama, E. & French, K.** (2015). *A Five-Factor Asset Pricing Model.* Journal of Financial Economics, 116(1), 1–22.
4. **Jegadeesh, N. & Titman, S.** (1993). *Returns to Buying Winners and Selling Losers.* Journal of Finance, 48(1), 65–91.
5. **Sloan, R.** (1996). *Do Stock Prices Fully Reflect Information in Accruals and Cash Flows about Future Earnings?* The Accounting Review, 71(3), 289–315.

---

*Erstellt für den NASDAQ-100 Cheapest Quality Screener v10.*
*Letzte Aktualisierung: März 2026.*