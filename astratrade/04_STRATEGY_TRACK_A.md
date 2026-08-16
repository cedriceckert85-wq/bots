# 04 — Track A: Market Exposure (SPY vs BIL)

Zurück: [[00_HOME]] · Verwandt: [[05_STRATEGY_TRACK_B]], [[06_STRATEGY_TRACK_C]], [[12_PORTFOLIO_CONSTRUCTION]]

**Primärer V1-Track.** Ziel: Schätzung des zukünftigen Excess Return von SPY gegenüber
BIL und Ausgabe einer Ziel-Marktexposure ∈ [0 %, 100 %].

---

## 1. Ökonomische Hypothese und Mechanismus

Markt-Timing im engen Sinn (Punktprognose des Returns) ist nach breiter Evidenz kaum
möglich. Belastbarer ist **Risiko-Timing**:

- **Volatility Targeting / Volatility-Managed Portfolios:** Skalierung der Exposure
  invers zur realisierten Volatilität verbessert risikoadjustierte Kennzahlen, weil
  Volatilität persistent (clusternd) ist, erwartete Returns aber kaum kurzfristig
  prognostizierbar sind. Kernliteratur: Moreira/Muir, *Volatility-Managed Portfolios*,
  Journal of Finance 2017; Harvey et al., *The Impact of Volatility Targeting*, JPM 2018.
  [FAKT, Primärliteratur; Ergebnisse regimeabhängig, siehe kritische Replikationen u.a.
  Cederburg et al. 2020 — Nutzen v.a. in Krisenregimen, nicht als konstante Alpha-Quelle.]
- **Zeitreihen-Momentum / Trendfolge:** 10-Monats-/200-Tage-Regeln reduzieren Drawdowns
  deutlich bei ähnlicher CAGR (Faber, *A Quantitative Approach to Tactical Asset
  Allocation*, JWM 2007; Moskowitz/Ooi/Pedersen, *Time Series Momentum*, JFE 2012).
  Mechanismus: verhaltensbasierte Unterreaktion + langsame Kapitalflüsse; Kosten: Whipsaw
  in Seitwärtsmärkten, Tracking-Underperformance in starken Bullenmärkten.
- **Downside-Schutz als eigentliches Produkt:** Das realistische Ziel von Track A ist
  nicht „SPY schlagen", sondern **vergleichbare CAGR bei deutlich reduziertem Maximum
  Drawdown und Volatilität** — das ist die einzige Behauptung, die die Literatur robust trägt.

**[EMPFEHLUNG, Confidence: hoch]** Track A wird als *Risiko-Timing-Track* definiert,
nicht als Return-Prognose-Track. Acceptance Gates werden auf risikoadjustierte Kennzahlen
und Drawdown gesetzt, nicht auf Outperformance der CAGR.

## 2. Target-Definition

- **Primäres Target (V1):** binäres/gestuftes Regime-Label ist verboten als direktes
  Trainingsziel (Leakage-anfällig). Stattdessen: `y = ExcessReturn(SPY_TR − BIL_TR)` über
  Horizont h ∈ {21, 63} Handelstage, als Regression UND als P(y>0)-Klassifikation.
- **Sekundäres Target:** realisierte Vorwärts-Volatilität über 21 Tage (für Vol-Targeting).
- Alle Targets auf **Total-Return-Basis** (Dividenden reinvestiert, [[17_DUAL_LEDGER]]).
- Überlappende Labels ⇒ **Purging + Embargo** zwingend ([[09_RESEARCH_PLATFORM]] §4).

## 3. Feature-Kandidaten (alle Point-in-Time, Quellen in [[07_MARKET_DATA]])

| Gruppe | Features | PIT-Risiko |
|---|---|---|
| Trend | Preis vs SMA(50/100/200), 12-1-Momentum, 52W-Hoch-Abstand | gering |
| Volatilität | realisierte Vol (5/21/63d), Vol-of-Vol, Parkinson/GK aus OHLC | gering |
| Vol-Markt | VIX-Level, VIX-Termstruktur (VIX/VIX3M), [ANNAHME: via CBOE/FRED verfügbar] | mittel (Publikationszeitpunkt prüfen) |
| Zins/Makro | 3M/10Y-Spread, 2s10s, Fed Funds (FRED, ALFRED für PIT-Vintages) | hoch ohne ALFRED — nur ALFRED-Vintage-Daten zulässig |
| Kreditrisiko | HY-OAS (FRED) | mittel |
| Marktbreite | % Sektoren über 200d-SMA (aus Track-B-Universum, nur als Feature, keine Track-Vermischung der Portfolios) | gering |
| Kalender | Monat, Turn-of-Month, FOMC-Tage [ANNAHME: Kalender manuell gepflegt] | gering |

**[REGEL-konform]** Marktbreite nutzt Sektordaten nur als *Feature* für Track A; die
Portfolios bleiben getrennt.

## 4. Modell-Leiter (einfach → komplex, jede Stufe muss die vorige schlagen)

1. **B0 — Buy & Hold SPY** (Benchmark, kein Modell).
2. **B1 — 200-Tage-Regel:** Exposure 100 % wenn Close > SMA200, sonst 0 %. Mit 1–2 %
   Hysterese-Band gegen Whipsaw.
3. **B2 — Vol-Targeting:** `w = clip(σ_target / σ_realized_21d, 0, 1)`, σ_target ≈ 12 %
   p.a. [ANNAHME, zu kalibrieren].
4. **B3 — Kombination B2 × B1** (Trend-Gate auf Vol-Target).
5. **M1 — Logistische Regression / ElasticNet** auf Feature-Set, Ziel P(Excess>0).
6. **M2 — Gradient Boosting (LightGBM)** mit monotonen Constraints wo ökonomisch
   begründbar; Kalibrierung via Isotonic/Platt auf separatem Fold.
7. **M3 — Ensemble B3+M1+M2** mit Abstention: bei |P−0,5| < δ keine Positionsänderung.

**Gate-Regel:** Stufe *n* wird nur weiterverfolgt, wenn sie Stufe *n−1* nach Kosten in
Walk-Forward über ≥ 3 Subperioden in Deflated Sharpe / MDD verbessert
([[09_RESEARCH_PLATFORM]] §6). Transformer/RNN/RL: **nicht in V1** — Datenmenge (≈ 8.000
Daily-Beobachtungen, hoch autokorreliert) rechtfertigt die Varianz nicht; Neubewertung
frühestens nach M2-Ergebnissen (ADR-Verweis [[26_ADR_INDEX]]).

## 5. Von Prediction zu Exposure

```
prediction (P, μ̂, σ̂) 
  → raw_exposure = f(P) mit f monoton, z.B. gestuft {0, 0.33, 0.66, 1.0}
  → vol_scaled  = min(raw_exposure, σ_target/σ̂)
  → smoothed    = EWMA(vol_scaled, λ) 
  → banded      = keine Änderung wenn |smoothed − current_weight| < 5 pp   (No-Trade-Band)
  → target_weight[SPY] = banded; target_weight[BIL] = 1 − banded
```

Turnover-Kontrolle: erwarteter Turnover < 400 % p.a. brutto [ANNAHME, im Backtest zu
verifizieren]; No-Trade-Band und gestufte Exposure sind die primären Regler.

## 6. Validierung und Gates (Zusammenfassung, Details [[09_RESEARCH_PLATFORM]])

- Walk-Forward: Training expandierend, Test 1 Jahr, Schritt 1 Jahr, ab 2010; 2020-Crash
  und 2022-Bärenmarkt müssen in Testfenstern liegen.
- Lockbox: **letzte 24 Monate + zufällig gewählte 12-Monats-Periode** werden bis zum
  finalen Gate nicht angefasst (Definition und Öffnungsprotokoll in [[09_RESEARCH_PLATFORM]] §7).
- Research Gate A→Paper: Deflated Sharpe > 0 (p < 0,05) gegen B1 UND B2; MDD < 0,8 × MDD(SPY);
  Ergebnis robust unter 2× Kostenannahme und 1-Tag-Ausführungsverzögerung.
- Paper Gate → Shadow: 3 Monate Paper, Tracking-Error Paper vs Backtest-Erwartung
  innerhalb definierter Bänder; 0 ungeklärte Reconciliation-Breaks.
- Live Gate: alle Blocker BL-01..04 aus [[02_REQUIREMENTS]] geschlossen.

**Keine fiktiven Backtestwerte:** Alle Zahlen oben sind Schwellenwerte/Annahmen, keine
Ergebnisse. Ergebnisse existieren erst nach Phase 3.
