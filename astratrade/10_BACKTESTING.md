# 10 — Backtesting: Build-vs-Buy, Engine-Architektur, Kostenmodell

Zurück: [[00_HOME]] · Verwandt: [[09_RESEARCH_PLATFORM]], [[26_ADR_INDEX]] (ADR-002), [[29_SOURCE_LEDGER]] (BT-Claims)

## 1. Recherchierter Stand der Frameworks (2026-08-15, Details im Source Ledger)

| Framework | Status | PIT | Corp. Actions | OPG/Auction | Wartungsrisiko |
|---|---|---|---|---|---|
| vectorbt 1.1 (OSS „Community Edition") | aktiv; Lizenz jetzt Apache-2.0 **mit Commons Clause** | – | – | – | mittel (Ein-Personen + PRO-Überbau) |
| backtrader | **letztes Release 2023-04, faktisch verwaist**, GPL-3.0 | – | – | +(cheat_on_open) | hoch |
| zipline-reloaded 3.1.1 (2025-07) | gepflegt, langsam (1 Rel./Jahr), Apache-2.0 | ++ (Preise/CA via Adjustment-Overlay) | ++ | – (custom Blotter nötig) | mittel |
| QuantConnect LEAN | sehr aktiv, Apache-2.0 | ++ (Map-/Factor-Files) | ++ | **++ nativer MarketOnOpenOrder** | niedrig; aber Datenformat-Lock-in |
| NautilusTrader v1.231 / v2-RC | sehr aktiv, LGPL-3.0 | – | – | + (OPG-TIF, EOD-Equity-Pfad wenig erprobt) | niedrig-mittel (v1→v2-Migration) |
| bt 1.2 | aktiv, MIT | – | – | – | niedrig-mittel |
| qf-lib 4.0 | gepflegt, klein | + | ? | + (Open-Events) | mittel-hoch |
| skfolio 0.20 | sehr aktiv, BSD-3 | (CV-Methoden: CombinatorialPurgedCV, DSR) | n/a | n/a | niedrig |

mlfinlab ist proprietär (kein PyPI mehr); skfolio ist der gepflegte OSS-Ersatz für
Purged-CV/Deflated-Sharpe [FAKT, Source Ledger LDP-1/2].

## 2. Build-versus-Buy-Entscheidungsmatrix

Anforderungen von ASTRATRADE: Daily-Frequenz, 1–12 ETFs je Track, Whole Shares,
Opening-Auction-Fill, Total-Return-Accounting, Determinismus, Live-Parität der
*Entscheidungslogik* (nicht der Ausführungssimulation), Kosten-/Slippage-Stress.

| Kriterium (Gewicht) | Eigenbau „schlanke Portfolio-Engine" | zipline-reloaded | LEAN | NautilusTrader |
|---|---|---|---|---|
| Auction-Fill-Semantik (hoch) | exakt modellierbar | custom nötig | nativ | vorhanden, EOD-Pfad riskant |
| PIT/CA (hoch) | über eigene Bitemporal-DB ([[08_DATA_CONTRACTS]]) — ohnehin Pflicht | gut, aber Bundle-Zwang | gut, aber Format-Lock-in | selbst bauen |
| Live-Parität Entscheidungslogik (hoch) | **identischer Code Research/Live** (gleiche Library) | getrennter Livepfad | QC-Cloud-Gravitation | gut, aber Overkill |
| Komplexität des Problems (hoch) | gering: ≤ 12 Assets, 1 Entscheidung/Tag, 1 Ordertyp | Engine-Komplexität ≫ Problem | Engine+C# ≫ Problem | Engine ≫ Problem |
| Wartungsrisiko (mittel) | eigenes Risiko, aber kleiner Code (~2–4 kLOC) | Fremdrisiko mittel | niedrig | mittel (v2-Migration) |
| Aufwand initial (mittel) | ~15–25 PT | ~10 PT Integration + Bundles | ~15 PT + Datenkonverter | ~20 PT |

**[ENTSCHEIDUNG, ADR-002, Confidence hoch] Hybrid:**

1. **Eigene, schlanke, deterministische Daily-Portfolio-Engine** (`libraries/astra-backtest`)
   als System of Record für alle Gate-Entscheidungen. Begründung: Das Problem (täglicher
   Ziel-Gewichtsvektor, Fill zum Auktions-Open, Whole Shares, TR-Accounting) ist klein
   genug, dass eine Engine mit vollständiger Testabdeckung billiger ist als die
   Anpassung eines Frameworks; nur so ist die Auction-/Whole-Share-/BIL-Semantik exakt
   und die **Entscheidungslogik im Live-System identisch** (gleiche Library, [[14_EXECUTION_ENGINE]]).
2. **vectorbt** für schnelle Signal-Exploration im Research (keine Gate-Relevanz).
3. **Cross-Check-Pflicht:** Jedes Gate-Ergebnis wird von einer zweiten, unabhängigen
   Implementierung (bt oder zipline-reloaded) auf Portfolio-Return-Ebene nachgerechnet;
   Abweichung > 1 bp/Monat ⇒ Klärung vor Gate ([[09_RESEARCH_PLATFORM]] Validation Gate).
4. skfolio für Purged/Combinatorial CV und DSR; quantstats nur für Report-Plots.

Alternative (verworfen, Neubewertung falls Universum > 50 Instrumente oder Intraday):
LEAN als Komplettplattform — Trade-off: nativer MOO-Fill vs Datenformat-Lock-in,
C#-Debugging-Grenze und Cloud-Gravitation.

## 3. Engine-Design (astra-backtest)

- **Event-Schleife über Handelstage** (exchange_calendars, Version im Run-Manifest):
  `t-1 close → Features/Prediction → Target Weights → t open: Auktions-Fill → Accounting`.
- Zustand: Positionen (Whole Shares), Cash, Accruals; Dividenden fließen am Pay Date als
  Cash zu (Ex-Date reduziert TR-Benchmark korrekt); Splits verändern Stückzahl am Ex-Tag.
- Fill-Modell Default: Fill zum **offiziellen Opening-Print** (Daily-Open des SIP-Feeds)
  + Slippage-Modell §5; Auction-Miss-Simulation (Order zu spät ⇒ Fill zum Open+5min-VWAP
  [ANNAHME]) als Stressvariante.
- Determinismus: keine Wanduhr, kein RNG ohne Seed im Config; Ausgabe = Hash über
  (Orders, Fills, NAV-Reihe); Determinism-Test in CI ([[22_TEST_STRATEGY]] T-DET-01).
- Ausgabeartefakte: NAV-Reihe (TR), Trade-Blotter, Exposure-Reihe, Kostenaufriss,
  Metrik-Report — alles mit `dataset_version`/`code_version`/`config_version` gestempelt.

## 4. Verbotene Vereinfachungen (Engine erzwingt)

- Kein Fill zum selben Close, aus dem das Signal stammt (t-close→t-close verboten;
  Standard ist t−1-close-Entscheidung → t-open-Fill; „nicht verfügbare Schlusskurse").
- Keine fraktionalen Stücke; Rundung deterministisch (floor auf Whole Shares, Rest BIL/Cash).
- Kein Handel an Feiertagen/Halbtagen ohne Kalenderprüfung; Half-Days mit eigener
  Auktionszeit getestet.
- Kein Zugriff auf Bars mit `as_of > decision_time` (Engine liest nur PIT-Snapshots).

## 5. Kosten- und Slippage-Modell (je Instrument, konfigurierbar)

`cost_roundtrip = commission (0 bei Alpaca [FAKT, zu verifizieren je Kontotyp]) +
half_spread + auction_impact`. Defaults [ANNAHME, im Paper Trading zu kalibrieren]:
SPY/IEF/TLT/GLD/IWM: half_spread 0,5–1 bp; Sektor-ETFs: 1–2 bps; BIL: 1 bp;
auction_impact = 0 für Ordergrößen < 0,01 % des Ø-Auktionsvolumens, sonst
Quadratwurzel-Modell. Regulatorische Gebühren (SEC/TAF auf Verkäufe) werden modelliert.
Stresstests: ×0,5/×1/×2/×4 auf Gesamtkosten; Gate verlangt Robustheit bei ×2
([[09_RESEARCH_PLATFORM]] §8).

## 6. Golden-Dataset-Tests

Kuratiertes Mini-Universum (SPY 2020-Crash-Monat, ein Split-Fall [z.B. GLD-frei, dafür
Test-Fixture], ein Dividenden-Quartal) mit **von Hand nachgerechneten** Soll-Ergebnissen
(NAV, Fills, Dividenden-Cashflows) als Regressionstest der Engine — Pflicht vor jedem
Engine-Release ([[22_TEST_STRATEGY]] §3).
