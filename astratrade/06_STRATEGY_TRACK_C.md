# 06 — Track C: Multi Asset (SPY, IWM, TLT, IEF, GLD, BIL)

Zurück: [[00_HOME]] · Verwandt: [[04_STRATEGY_TRACK_A]], [[05_STRATEGY_TRACK_B]]

## 1. Ökonomische Hypothese

Taktische Multi-Asset-Allokation stützt sich auf zwei robuste Befunde:

- **Time-Series-Momentum über Assetklassen** (Moskowitz/Ooi/Pedersen 2012; Faber 2007
  „GTAA"): 10M-SMA-/12-1-Momentum-Filter je Assetklasse reduziert Drawdowns über
  Aktien, Anleihen, Gold hinweg.
- **Risk Parity / inverse Vol-Gewichtung:** Anleihen und Gold haben strukturell andere
  Volatilität als Aktien; naive Equal-Weights sind implizit aktienrisikodominiert.
- **Warnung [FAKT, 2022]:** Die Aktien-Anleihen-Korrelation ist regimeabhängig; 2022
  fielen SPY und TLT gemeinsam stark. Ein Modell, das auf negativer Korrelation als
  Konstante beruht, ist abzulehnen. Korrelation muss als rollierendes, PIT-berechnetes
  Feature/Constraint behandelt werden.

## 2. Konstruktion

- Baseline B1: Faber-GTAA-Variante — je Asset 1/5-Budget, investiert wenn Preis > 10M-SMA,
  sonst Budget in BIL.
- B2: Inverse-Vol-Gewichtung der Momentum-positiven Assets, Vol-Target 8–10 % p.a.
  [ANNAHME, zu kalibrieren], Rest BIL.
- M1: GBM/ElasticNet auf Asset-Panel (Momentum-, Vol-, Carry-Proxy-, Zins-Features)
  mit Ranking-Target — nur bei nachweisbarem Mehrwert gegenüber B2.
- Constraints: max 40 % je Nicht-Aktien-Asset, max 70 % Aktien gesamt (SPY+IWM),
  No-Trade-Band 5 pp, Turnover-Ziel < 250 % p.a. [ANNAHME].

## 3. Benchmark

**[ENTSCHEIDUNG]** Primär: statisches 60/40-Portfolio (60 % SPY / 40 % IEF, monatlich
rebalanciert, TR, selbst berechnet und versioniert). Sekundär: Equal-Weight-5-Asset-Mix
(je 20 % SPY/IWM/TLT/IEF/GLD, monatlich rebalanciert). Begründung: 60/40 ist der
Standard-Vergleichsmaßstab für taktische Allokation; der EW-Mix isoliert den
Timing-/Gewichtungsbeitrag im eigenen Universum.

## 4. Spezifika und Gates

- GLD und TLT/IEF haben andere Handelscharakteristika (Spreads eng, aber
  Auktionsvolumina kleiner als SPY) ⇒ Slippage-Modell je Instrument ([[10_BACKTESTING]] §5).
- Treasury-ETF-Renditen sind zinsregimeabhängig; Subperioden-Tests müssen 2013
  (Taper), 2020, 2022–2023 (Zinsschock) einzeln ausweisen.
- Eigenes Risikobudget, eigene Portfolio-ID, eigene Gates — analog Track B.
- Research Gate: Verbesserung von Sharpe UND MDD gegenüber 60/40 nach Kosten in
  Walk-Forward; Robustheit gegen ±25 % Parametervariation (SMA-Länge, Vol-Fenster).
