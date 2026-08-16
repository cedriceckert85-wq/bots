# 09 — Research-Plattform, Validierung und Anti-Leakage

Zurück: [[00_HOME]] · Verwandt: [[08_DATA_CONTRACTS]], [[10_BACKTESTING]], [[11_ML_ARCHITECTURE]]

## 1. Architektur des Research-Pfads

```
bars(raw) + corporate_actions ──► Dataset Builder ──► dataset_versions (Parquet, versioniert)
                                        │
                              feature_definitions (Registry, Code + Doku)
                                        │
                    Research Env (JupyterLab, read-only auf Datasets)
                                        │
                    Backtest Engine ([[10_BACKTESTING]]) + Experiment Tracking (MLflow)
```

- Research-Umgebung hat **read-only**-Zugriff auf versionierte Datasets, keinen Zugriff
  auf Live-Datenbanken oder Broker-Keys ([[18_SECURITY]] Zone R).
- Jedes Experiment referenziert `dataset_version` + `code_version` + `config_version`;
  Notebooks ohne diese Referenzen gelten als nicht zitierfähig.

## 2. Dataset Builder

- Input: Symbolliste aus `universe_memberships` **zum jeweiligen historischen Datum**
  (kein heutiges Universum auf die Vergangenheit projizieren ⇒ Survivorship-/Selection-Bias).
- Output: unveränderliche Parquet-Datasets `s3://datasets/{track}/{dataset_version}/`
  mit Manifest (Input-Manifeste, Feature-Def-Versionen, Zeitraum, Hash).
- Feature-Berechnung ausschließlich aus Daten mit `as_of ≤ decision_time`; der Builder
  erzwingt das technisch, indem er pro Entscheidungstag nur den bitemporalen Snapshot
  lädt (As-of-Join), nicht die Volltabelle.
- Normalisierung (z-Scores etc.) wird **im Trainings-Fold gefittet** und als Parameter
  gespeichert — nie über den Gesamtzeitraum (Leakage über Normalisierung).

## 3. Feature Registry

`feature_definitions(feature_id PK, name, version, code_ref, inputs[], lookback,
publikationsverzögerung, unit, owner, created_at, deprecated_at)`. Eine Feature-Version
ist unveränderlich; Änderungen ⇒ neue Version. Cross-Section-Features (z.B. Ranks über
das Track-B-Universum) deklarieren ihr Universum explizit, damit Universe-Leakage
(Ranks über später hinzugekommene Symbole) im Test T-LEAK-04 erkennbar ist.

## 4. Validierungsprotokoll (verbindlich)

1. **Splits:** ausschließlich zeitbasiert; bei Panels (Track B/C) date-based über alle
   Symbole gleichzeitig (kein Symbol-Split).
2. **Walk-Forward:** expandierendes Training, 12M-Test, 12M-Schritt; zusätzlich
   rollierendes Fenster als Robustheitsvariante.
3. **Purged K-Fold + Embargo** (López de Prado, *Advances in Financial ML*, 2018) für
   Hyperparameter-Suche innerhalb des Trainingsfensters: Purge = Label-Horizont h,
   Embargo = 5 Handelstage [ANNAHME, h-abhängig].
4. **Hyperparameter-Optimierung** (Optuna) sieht nie Testfenster; die Anzahl aller
   jemals evaluierten Konfigurationen wird im Experiment-Tracker gezählt und fließt in
   Deflated Sharpe / Multiple-Testing-Korrektur ein (Bailey/López de Prado, *The
   Deflated Sharpe Ratio*, 2014; White Reality Check/SPA als Alternative).
5. **Bias-Checkliste je Studie** (muss im Experiment-Report abgehakt sein): Look-ahead,
   Survivorship, Selection, Corporate-Action, Revision (nur ALFRED-Vintages für Makro),
   Backfill (zeitvariables Universum), Snooping (Konfigurationszähler), Leakage über
   Normalisierung/Universe/Cross-Section/HPO, Fill-Annahmen, Kosten (Basis + 2×-Stress),
   Auction-Annahmen ([[10_BACKTESTING]] §4).

## 5. Automatisierte Leakage-Tests (CI-blockierend, Details [[22_TEST_STRATEGY]])

- T-LEAK-01 „Shuffle-Target": Modell auf permutierten Targets darf keine
  Out-of-Sample-Performance zeigen (sonst Pipeline-Leak).
- T-LEAK-02 „Zeitmaschine": Dataset für Entscheidungstag t wird einmal mit `as_of=t`
  und einmal mit `as_of=heute` gebaut; Features müssen für t identisch sein, sonst
  fließt revidierte Information ein.
- T-LEAK-03 „Feature-Timing": synthetischer Datensatz mit bekanntem Einspielzeitpunkt;
  Feature darf erst nach Publikationsverzögerung erscheinen.
- T-LEAK-04 „Universe-PIT": Backtest 2014 darf XLC nicht kennen.
- T-LEAK-05 „Normalisierung": Scaler-Parameter dürfen sich nur aus Trainingsfold
  reproduzieren lassen.

## 6. Metriken und Forschungsstandards

Pflichtmetriken je Experiment (Formeln in `libraries/astra-metrics`):
CAGR, ann. Vol, Sharpe (rf = BIL-TR), Sortino, Calmar, MaxDD + DD-Dauer, Ulcer Index,
ES(95), Hit Rate, Profit Factor, Turnover, Ø-Exposure, Alpha/Beta/TE/IR vs
Track-Benchmark, Kosten-Breakeven (bps Roundtrip, bei denen Sharpe = Benchmark),
Slippage-Sensitivität (0,5×/1×/2×/4×), Subperioden- und Regime-Tabelle (Bull/Bär/
Hochvol-Regime via realisierter Vol-Terzile).

Statistische Absicherung: Block-Bootstrap-Konfidenzintervalle (Blocklänge ≈ 21 Tage)
für Sharpe/CAGR; **Deflated Sharpe Ratio** mit tatsächlichem Trial-Zähler; Probability
of Backtest Overfitting (CSCV, Bailey et al. 2015) für Modellvergleiche; Parameter-
Sensitivity-Heatmaps; Feature-/Modell-Ablation. Delayed-Execution-Test (Ausführung t+1
Open statt t Open) und Missing-Data-/Feed-Degradation-Test sind Pflicht vor jedem Gate.

**Es werden keine Backtest-Ergebnisse erfunden.** Diese Datei definiert Methoden und
Schwellen; Zahlen entstehen erst in Phase 2/3.

## 7. Lockbox / Holdout

- Definition bei Projektstart (Phase 0, vor jeder Modellarbeit), notariell einfach:
  Commit einer Datei `lockbox.yaml` mit den ausgeschlossenen Zeiträumen + Hash im
  Audit Log. Vorschlag: **letzte 24 Monate ab Projektstart** + **12 zufällige Monate
  aus 2012–2019** (Seed im Commit).
- Zugriffskontrolle: Dataset Builder weigert sich, Lockbox-Zeiträume in Research-
  Datasets aufzunehmen (`lockbox_guard`); Ausnahme nur über signierten
  Freigabe-Eintrag in `audit_events`.
- Öffnungsprotokoll: Lockbox darf erst geöffnet werden, wenn alle Research-/Validation-
  Gates dokumentiert bestanden sind; Öffnung wird geloggt; danach gilt die Periode
  dauerhaft als „touched" und wird in jedem Report so ausgewiesen. Eine zweite
  „frische" Bewertung ist nur durch neu verstreichende Zeit möglich.

## 8. Gate-Katalog (messbare Pass/Fail-Kriterien)

| Gate | Kriterien (alle müssen erfüllt sein) |
|---|---|
| Research Gate | Bias-Checkliste vollständig; Baseline-Leiter eingehalten; DSR > 0 (p<0,05) vs Track-Baseline; robust bei 2× Kosten und t+1-Ausführung; PBO < 0,2 |
| Validation Gate | unabhängige Re-Implementierung der Kernmetriken (Zweitrechnung) weicht < 1 bp ab; Determinismus-Test bestanden; Leakage-Tests grün |
| Paper Gate | 60 Handelstage Paper; Realized-vs-Expected-Tracking innerhalb Band (Slippage < Modellannahme + 50 %); 0 offene Reconciliation-Breaks; alle Runbooks getestet |
| Shadow Gate | 20 Handelstage Shadow parallel zu Paper; Entscheidungen identisch zu Offline-Rechnung (Hash-Gleichheit) |
| Small-Capital-Live Gate | Blocker BL-01..04 geschlossen; Kill-Switch-Drill durchgeführt; Limits konfiguriert und getestet |
| Scale-up Gate | ≥ 6 Monate Live; realisierte Slippage/Tracking im Band; kein Sev-1-Incident offen; Kapitalerhöhung max ×2 pro Schritt |
| Rollback Gate | definierte Trigger ([[13_RISK_ENGINE]] §5) ⇒ automatische Rückstufung auf Vorgänger-Champion oder BIL-Safe-State |
| Model-Retirement Gate | Prediction-Drift/Performance unter Schwelle über 60 Tage ⇒ Retirement-Workflow ([[11_ML_ARCHITECTURE]] §6) |
