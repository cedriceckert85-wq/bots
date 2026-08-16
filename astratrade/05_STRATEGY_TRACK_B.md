# 05 — Track B: Sector Rotation (11 Sector SPDRs + BIL)

Zurück: [[00_HOME]] · Verwandt: [[04_STRATEGY_TRACK_A]], [[06_STRATEGY_TRACK_C]]

Universum: XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY + BIL.
**Wichtig:** XLC existiert erst seit Juni 2018, XLRE seit Oktober 2015 [FAKT, Fondsauflage
State Street; im Source Ledger]. Das Universum ist also **zeitvariabel** —
`universe_memberships` mit Gültigkeitszeiträumen ist zwingend ([[08_DATA_CONTRACTS]]),
sonst entsteht Backfill-Bias: vor 2015/2018 existieren nur 9 bzw. 10 Sektoren, und die
GICS-Umklassifizierung 09/2018 (Tech→Communication Services) verändert die
Sektorzusammensetzung rückwirkend nicht in den ETF-Preisen, wohl aber in jeder
fundamentalen Interpretation.

## 1. Ökonomische Hypothese

- **Cross-Section-Momentum:** relative 3–12-Monats-Stärke persistiert (Jegadeesh/Titman
  1993; für Industrien: Moskowitz/Grinblatt, *Do Industries Explain Momentum?*, JF 1999).
- **Sektor-Rotation über den Konjunkturzyklus** ist als narrative Strategie populär, aber
  als PIT-Signal schwach belegt — Konjunkturphasen sind erst ex post datierbar.
  **[EMPFEHLUNG]** Kein NBER-/Zyklus-Feature in V1; nur preisbasierte + Zins-Features
  mit ALFRED-Vintages.
- Erwartung konservativ: Sektor-Momentum ist eine **schwächere** Anomalie als
  Einzelaktien-Momentum (weniger Dispersion, 11 Assets). Track B ist daher
  Kapazitäts-/Diversifikationsbaustein, kein Haupt-Alpha-Träger.

## 2. Signal- und Portfolio-Konstruktion

- Score je Sektor: 12-1-Momentum (primär), 6-1 und 3-1 als Ensemble-Komponenten,
  volatilitätsadjustiert (Score/σ_63d).
- Ranking → Zielgewichte: Top-k (k=3..5) equal- oder score-weighted; Sektoren mit
  negativem absolutem Momentum (< BIL-Return über 12M) werden durch BIL ersetzt
  („Dual Momentum"-Gate, Antonacci 2014 [Sekundärquelle, Confidence mittel]).
- Constraints: max 30 % je Sektor, min Haltefrist über No-Trade-Band + Hysterese im
  Ranking (Wechsel nur wenn Rangdifferenz ≥ 2), Ziel-Turnover < 300 % p.a. [ANNAHME].
- Modell-Leiter analog Track A: Ranking-Heuristik (B1) → Vol-Adjustierung (B2) →
  Learning-to-Rank/GBM auf Cross-Section-Features (M1) — M1 nur bei nachweisbarem
  Mehrwert.

## 3. Benchmark-Entscheidung (verbindlich festzulegen)

Verglichen wurden:

| Kandidat | Pro | Contra |
|---|---|---|
| SPY | investierbar, Kapitalmaßstab | cap-weighted ⇒ misst Sektor-*Auswahl* nicht sauber; Größen-Bias |
| Equal-Weight-Mittel der 11 Sektoren (täglich rebalanciert, Total Return) | isoliert die eigentliche Fähigkeit (Cross-Section-Selektion); kein Größen-Bias | nicht direkt investierbar; muss selbst korrekt (PIT, zeitvariables Universum!) berechnet werden |
| RSP (Equal-Weight S&P 500) | investierbar | misst Equal-Weight-Prämie, nicht Sektorauswahl |

**[ENTSCHEIDUNG, Confidence hoch]** Primärer Benchmark = **selbstberechneter
Equal-Weight-Sektor-Index (TR, zeitvariables Universum, PIT)**; SPY (TR) als sekundäre
Kapital-Benchmark. Ein Track-B-Modell muss den EW-Index nach Kosten schlagen (Selektionsfähigkeit)
UND darf gegen SPY kein inakzeptables Drawdown-Profil zeigen. Beide Reihen werden als
`benchmark_series` versioniert gespeichert.

## 4. Spezifische Risiken und Gates

- Konzentrationsrisiko: Top-3-Portfolio hat hohe idiosynkratische Sektorrisiken ⇒
  Korrelations-Check im Risk Engine ([[13_RISK_ENGINE]] §3, Check R-22).
- XLC/XLRE-Historie kurz ⇒ Walk-Forward erst ab 2019 mit vollem Universum; frühere
  Perioden nur mit 9/10-Sektor-Universum und entsprechend gekennzeichnet.
- Research Gate: Information Ratio vs EW-Benchmark > 0 mit Deflated-Sharpe-Korrektur
  über die getestete Konfigurationsanzahl; Turnover-Kosten-Breakeven ausgewiesen.
- Eigene Risikobudgets, eigenes Paper-Subkonto bzw. getrennte Portfolio-ID — keine
  Vermischung mit Track A ([[02_REQUIREMENTS]] REGEL 1).
